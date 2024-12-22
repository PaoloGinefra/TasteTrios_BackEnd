from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from flask_cors import CORS
from elasticsearch import Elasticsearch
from ElasticQueries import elasticQueries

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Get credentials from environment variables
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
bonsai_url = os.getenv("BONSAI_URL")

# Create a Neo4j driver
driver = GraphDatabase.driver(uri, auth=(username, password))

# Create an Elasticsearch client
es = Elasticsearch(bonsai_url,
                   verify_certs=True)


@app.route("/api/neo4j/data", methods=["GET"])
def get_neo4j_data():
    try:
        # Create a session and run a query
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN n LIMIT 5")
            data = [record['n'] for record in result.data()]

        response = jsonify(data)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/neo4j/checkIngredient", methods=["POST"])
def check_ingredient():
    """Check if an ingredient exists in the database.
    The ingredient is passed in the request body as a JSON object with the key "ingredient".

    Returns:
        A JSON object with a key "exists" that is True if the ingredient exists in the database and False
    """
    try:
        # Create a session and run a query
        with driver.session() as session:
            ingredient = request.json['ingredient']
            result = session.run(
                "MATCH (n:Ingredient) WHERE n.name = $ingredient RETURN n", ingredient=ingredient)
            data = [record['n'] for record in result.data()]

        # Return whether the ingredient is in the database
        exists = len(data) > 0
        response = jsonify({"exists": exists})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/neo4j/checkIngredient", methods=["OPTIONS"])
def check_ingredient_options():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/api/neo4j/matchIngredients", methods=["POST"])
def matchIngredients():
    """Returns a list of recipes that must contain at least one of the ingredients in the list. The results are sorted by the number of ingredients that match the query.
    The ingredients are passed in the request body as a JSON object with the key "ingredients".
    A limit parameter can be passed in the request body to limit the number of results.

    Returns:
        A JSON object with a key "recipes" that is a list of recipes matches. For each recipe match, the object contains the keys
          "matchingScore" (the number of ingredients that match the query) and "recipe" (the recipe object).
    """
    try:
        # Create a session and run a query
        with driver.session() as session:
            ingredients = request.json['ingredients']
            limitString = ""
            if ("limit" in request.json):
                limit = request.json['limit']
                limitString = f" LIMIT {limit}"

            result = session.run(
                """
                MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
                WHERE i.name IN $ingredients
                WITH r, count(i) AS matchingScore, COLLECT(i.name) AS matchingIngredients
                RETURN r, matchingScore, matchingIngredients ORDER BY matchingScore DESC
                """
                + limitString, ingredients=ingredients)
            data = [{"matchingScore": record['matchingScore'], "recipe": record['r'], "matchingIngredients": record['matchingIngredients']}
                    for record in result.data()]

        response = jsonify({"recipes": data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/neo4j/matchIngredients", methods=["OPTIONS"])
def matchIngredients_options():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/api/elasticsearch/matchIngredients", methods=["POST"])
def matchIngredients_es():
    """Returns a list of recipes that must contain at least one of the ingredients in the list. The results are sorted by the number of ingredients that match the query.
    The ingredients are passed in the request body as a JSON object with the key "ingredients".
    A limit parameter can be passed in the request body to limit the number of results.

    Returns:
        A JSON object with a key "recipes" that is a list of recipes matches. For each recipe match, the object contains the keys
          "matchingScore" (the number of ingredients that match the query) and "recipe" (the recipe object).
    """
    try:
        # Create a session and run a query
        ingredients = request.json['ingredients']
        limit = request.json['limit']
        body = {
            "query": {
                "bool": {
                    "should": [{
                        "match": {
                            "RecipeIngredientParts": {
                                "query": " ".join(ingredients),
                                "operator": "or"
                            }
                        }
                    }]
                }
            }
        }
        result = es.search(index="recipeswithreviews", body=body, size=limit)
        data = [{"matchingScore": record['_score'], "recipe": record['_source']}
                for record in result['hits']['hits']]

        response = jsonify({"recipes": data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/elasticsearch/matchIngredients", methods=["OPTIONS"])
def matchIngredients_es_options():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/api/elasticsearch/matchIngredientsAnd", methods=["POST"])
def matchIngredientsAnd_es():
    """Returns a list of recipes that must contain the last ingredient in the list while it should contain at least one other ingredient. The results are sorted by the number of ingredients that match the query.
    The ingredients are passed in the request body as a JSON object with the key "ingredients".
    A limit parameter can be passed in the request body to limit the number of results.

    Returns:
        A JSON object with a key "recipes" that is a list of recipes matches. For each recipe match, the object contains the keys
          "matchingScore" (the number of ingredients that match the query) and "recipe" (the recipe object).
    """
    try:
        # Create a session and run a query
        ingredients = request.json['ingredients']
        limit = request.json['limit']
        body = {
            "query": {
                "bool": {
                    "filter": [
                        {"match":
                         {
                             "RecipeIngredientParts": ingredients[-1]
                         }
                         }
                    ],
                    "must": [
                        {
                            "match": {
                                "RecipeIngredientParts": {
                                    "query": " ".join(ingredients[:-1]),
                                    "operator": "or"
                                }
                            }
                        }
                    ]
                }
            }
        }
        result = es.search(index="recipeswithreviews", body=body, size=limit)
        data = [{"matchingScore": record['_score'], "recipe": record['_source']}
                for record in result['hits']['hits']]

        response = jsonify({"recipes": data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/elasticsearch/matchIngredientsAnd", methods=["OPTIONS"])
def matchIngredientsAnd_es_options():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/api/neo4j/getIngredients", methods=["POST"])
def getIngredients():
    """Returns a list of all the ingredients recessary for a recipe.
    The recipe is passed in the request body as a JSON object with the key "recipeId".

    Returns:
        A JSON object with a key "ingredients" that is a list of ingredients for the recipe.
    """
    try:
        # Create a session and run a query
        with driver.session() as session:
            recipe = request.json['recipeId']
            result = session.run(
                """
                MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
                WHERE r.id = $recipe
                RETURN COLLECT(i.name) AS ingredients
                """, recipe=recipe)
            data = result.single()['ingredients']

        response = jsonify({"ingredients": data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/neo4j/getIngredients", methods=["OPTIONS"])
def getIngredients_option():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/api/neo4j/mixAndMax", methods=["POST"])
def mixAndMax():
    """Returns a list of ingredients that can be used with the ingredients in the list to create many recipes.
    The ingredients are passed in the request body as a JSON object with the key "ingredients".
    The number of recipes and average rating of the recipes that can be made with the ingredients is calculated.
    The average number of the given ingredients in the recipes is also calculated.
    A limit parameter can be passed in the request body to limit the number of results.
    Returns:
        A JSON object with a key "ingredients" that is a list of objects with the keys "ingredient", "numRecipes", "avgRating" and "IngredientCompatibility".
    """

    try:
        # Create a session and run a query
        with driver.session() as session:
            ingredients = request.json['ingredients']
            limitString = ""
            if ("limit" in request.json):
                limit = request.json['limit']
                limitString = f" LIMIT {limit}"
            result = session.run(
                """
                WITH $providedIngredients AS ingredients
                // Find recipes that contain an existing ingredient and additional matched ingredients
                MATCH (i:Ingredient)<-[:CONTAINS]-(r:Recipe)-[:CONTAINS]->(i1:Ingredient)
                WHERE i.name IN ingredients AND NOT i1.name IN ingredients
                WITH DISTINCT r, i1.name AS matchedIngredient, ingredients, COUNT(distinct i) as availableMatchedIngredients

                // Match reviews for these recipes and calculate the average rating for each matched recipe
                MATCH (r)<-[:FOR]-(rev:Review)
                WITH matchedIngredient, r, AVG(rev.rating) AS avgRating, ingredients, availableMatchedIngredients

                // Count the number of unique recipes for each matched ingredient
                MATCH (r)-[:CONTAINS]->(i:Ingredient)
                WHERE i.name IN ingredients
                RETURN matchedIngredient, COUNT(DISTINCT r) AS recipeCount, AVG(avgRating) AS avgOfAvgRatings, AVG(availableMatchedIngredients) as IngredientCompatibility
                ORDER BY IngredientCompatibility * log10(recipeCount) DESC
                """
                + limitString, providedIngredients=ingredients)
            data = [record for record in result.data()]

        response = jsonify({"ingredients": data})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/neo4j/mixAndMax", methods=["OPTIONS"])
def mixAndMax_option():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers",
                         "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response


@app.route("/api/elasticsearch/queries", methods=["GET"])
def elastic_queries():
    """Run an ElasticSearch query based on the query number and the JSON body.
    The query number is passed as a query parameter.
    The JSON body should contain the key "limit" with the number of results to return.

    Returns:
        A JSON object with the results of the ElasticSearch query.
    """
    try:
        if ('queryNumber' not in request.args):
            return jsonify({"error": "No query number found"}), 400

        if ('limit' not in request.args):
            return jsonify({"error": "No limit found"}), 400

        queryNumber = int(request.args.get('queryNumber'))

        if (queryNumber < 0 or queryNumber >= len(elasticQueries)):
            return jsonify({"error": f"Invalid query number, it should be between 0 and {len(elasticQueries) - 1}"}), 400

        limit = int(request.args['limit'])

        if (limit < 0):
            return jsonify({"error": "Limit should be greater than 0"}), 400

        query = elasticQueries[queryNumber]

        result = es.search(index="recipeswithreviews", body=query, size=limit)

        if ('aggregations' not in result):
            data = [{"matchingScore": record['_score'], "recipe": record['_source']}
                    for record in result['hits']['hits']]
            response = jsonify({"recipes": data})
        else:
            data = result['aggregations']
            response = jsonify(data)

        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/elasticsearch/queries", methods=["OPTIONS"])
def elastic_queries_options():
    response = jsonify({"status": "OK"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@app.route("/")
def hello():
    return "Hello, World!"


# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
