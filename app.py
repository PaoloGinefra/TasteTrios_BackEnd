from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Get credentials from environment variables
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

# Create a Neo4j driver
driver = GraphDatabase.driver(uri, auth=(username, password))

# Define a route to fetch data from Neo4j


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


@app.route("/api/neo4j/getIngredients", methods=["POST"])
def getIngredients():
    """Returns a list of all the ingredients recessary for a recipe.
    The recipe is passed in the request body as a JSON object with the key "recipe".

    Returns:
        A JSON object with a key "ingredients" that is a list of ingredients for the recipe.
    """
    try:
        # Create a session and run a query
        with driver.session() as session:
            recipe = request.json['recipe']
            result = session.run(
                """
                MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
                WHERE r.name = $recipe
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


@app.route("/")
def hello():
    return "Hello, World!"


# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True)
