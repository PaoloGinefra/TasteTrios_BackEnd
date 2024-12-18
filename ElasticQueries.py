elasticQueries = [
    """
GET /recipeswithreviewsfinal/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "RecipeServings": {
              "gte": 2,
              "lte": 3
            }
          }
        }
      ],
      "should": [
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": {
                  "query": "romantic",
                  "boost": 2
                }
              }
            }
          }
        },
        {
          "match": {
            "Keywords": {
              "query": "romantic",
              "boost": 2
            }
          }
        },
        {
          "match": {
            "Description": {
              "query": "romantic",
              "boost": 2
            }
          }
        },
        {
          "range": {
            "AggregatedRating": {
              "gte": 3.5
            }
          }
        }
      ]
    }
  }
}
    """,
    """
    GET /recipeswithreviews/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "RecipeServings": {
              "gte": 10
            }
          }
        }
      ],
      "should": [
        {
          "match": {
            "Keywords": {
              "query": "party, large groups, gathering, celebration, event, buffet",
              "operator": "or",
              "boost": 2
            }
          }
        },
        {
          "match": {
            "RecipeCategory": {
              "query": "Dessert, Appetizer, Main, Party, Buffet",
              "operator": "or",
              "boost": 1.5
            }
          }
        },
        {
          "match": {
            "Description": {
              "query": "party, large groups, gathering, celebration, event",
              "operator": "or",
              "boost": 1.5
            }
          }
        },
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": {
                  "query": "party, celebration, gathering, event, buffet",
                  "operator": "or",
                  "boost": 3
                }
              }
            }
          }
        }
      ],
      "minimum_should_match": 1
    }
  }
}
""",
    """
GET /recipeswithreviews/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "RecipeInstructions": "microwave"
          }
        }
      ],
      "must_not": [
        {
          "match": {
            "Keywords": {
              "query": "oven pan pot fryer",
              "operator": "or"
            }
          }
        },
        {
          "match": {
            "RecipeInstructions": {
              "query": "oven pan pot fryer",
              "operator": "or"
            }
          }
        }
      ],
      "should": [
        {
          "match": {
            "Keywords": "microwave"
          }
        },
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": "microwave"
              }
            }
          }
        }
      ]
    }
  }
}
    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "RecipeIngredientParts": {
              "query": "chicken onion cheese",
              "operator": "and"
            }
          }
        },
        {
          "range": {
            "TotalTime": {
              "lte": 30
            }
          }
        }
      ]
    }
  }
}
    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "runtime_mappings": {
    "pcratio": {
      "type": "double", 
      "script": {
        "source": \"\"\"
          if (doc['Calories'].size() > 0 && doc['Calories'].value != 0) {
            emit(doc['ProteinContent'].value / doc['Calories'].value);
          }
        \"\"\"
      }
    }
  },
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "pcratio": {
              "gte": 0.2
              }
            }
          }
      ],
      "should": [
        {
          "match": {
            "Description": {
              "query": "healthy gym protein fit strong weight nutritious",
              "operator": "or"
            }
          }
        },
        {
          "match": {
            "Keywords": {
              "query": "healthy gym protein fit strong weight nutritious",
              "operator": "or",
              "boost": 3
            }
          }
        },
        {
          "match": {
            "RecipeCategory": {
              "query": "healthy gym protein fit strong weight nutritious",
              "operator": "or"
            }
          }
        },
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": {
                  "query": "healthy gym protein fit strong weight nutritious",
                  "operator": "or"
                }
              }
            }
          }
        }
      ]
    }
  }
}


    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "query": {
    "bool": {
      "must_not": [
        {
          "match": {
            "RecipeIngredientParts": {
              "query": "milk cheese lactose yogurt",
              "operator": "or"
            }
          }
        }
      ],
      "should": [
        {
          "match": {
            "Keywords": "lactose free"
          }
        },
        {
          "match": {
            "Description": "lactose free intolerant"
          }
        },
        {
          "match": {
            "RecipeCategory": "lactose free"
          }
        },
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": "lactose free intolerant"
              }
            }
          }
        }
      ]
    }
  }
}
    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "size": 1,
  "query":{
    "match": {
      "RecipeIngredientParts": "corn"
      }
    },
  "aggs": {
    "by_review_year": {
      "date_histogram": {
        "field": "DatePublished",
        "calendar_interval": "year",
        "format": "yyyy"
      }
    }
  }
}
    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "query": {
    "bool": {
      "must":[
        {"match": {"RecipeCategory": "Snacks"}},
        {"range": { "ProteinContent": { "gte": 20 } } }
      ],
      "should": [
        { "match": { 
            "Description": {
              "query": "healthy snack",
              "operator": "and"
            } } },
        {
          "nested": {
            "path": "Reviews",
            "query": {
              "match": {
                "Reviews.Review": {
                  "query": "healthy snack",
                  "operator": "and"
                }
              }
            }
          }
        },
        {
          "match": {
            "Keywords": {
              "query": "healthy snack"
            }
          }
        }
      ],
      "must_not": [
        { "match":{"RecipeCategory": "dessert"} },
        { "match":{"Keywords": "dessert"} }
      ]
    }
  }
}

    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "size": 2,
  "query": {
    "bool": {
      "must": [
        {"range": { "AggregatedRating": { "gte": 4} } },
        {"range": { "ReviewCount": { "gte": 10 } } },
        {"nested":{
          "path": "Reviews",
          "query": {
            "match": {
              "Reviews.Review": {
                "query": "great excellent good amazing awesome",
                "operator": "or"
            }
          }
        }}}
      ]
    }
  },
  "aggs": {
    "positive_sentiment_per_author": {
      "terms": {
        "field": "AuthorId"
      },
      "aggs": {
        "average_rating": {
          "avg": {
            "field": "AggregatedRating"
          }
        }
      }
    }
  }
}

    """,
    """
GET /recipeswithreviewsfinal/_search
{
  "query": {
    "bool": {
      "should": [
          {"match":
            {
              "Description": {
                "query": "college student cheap easy",
                "operator": "or"
              }
            }
          },
          {"match":
            {
              "Keywords": {
                "query": " college student cheap easy",
                "operator": "or"
              }
            }
          },
          {"match":
            {
              "RecipeCategory": {
                "query": "college student cheap easy",
                "operator": "or"
              }
            }
          },
          {"nested":{
          "path": "Reviews",
          "query": {
            "match": {
              "Reviews.Review": {
                "query": "college student cheap easy",
                "operator": "or"
            }
          }
        }}}
      ],
      "must_not": [
        {
          "range": {
            "TotalTime": {
              "gte": 60
            }
          }
        }
      ],
      "minimum_should_match": 1
    }
  }
}
    """
]
