# Beyo Purchase App – Flask Backend

This is the backend API for the **Beyo Purchase App**, a highly dynamic Flask-based system designed for full control over data management through API calls.  
It supports creation, updating, deletion, and querying of multiple models, including complex relationships, all via RESTful endpoints.

---

## 🚀 Key Features

- **Dynamic CRUD operations** for any model in the system  
- **Relationship management**: link, unlink, or create related objects dynamically  
- **Batch processing**: handle single objects or lists of objects in one API call  
- **Advanced validation**: ensures data integrity using Marshmallow schemas  
- **Error handling**: consistent structured responses for validation, database, and operational errors  
- **Highly configurable**: all operations are controllable via API payloads  
- **Supports transactions**: commits and rollbacks handled automatically  

---

## 🧰 Tech Stack

- **Python 3.11+**  
- **Flask** for REST API routing  
- **SQLAlchemy** for ORM and database interaction  
- **Marshmallow** for input validation  
- **Flask-Login** for authentication  
- **PostgreSQL** (or other SQLAlchemy-supported databases)  
- **psycopg2** for PostgreSQL database driver  

---

## ⚙️ API Overview

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/schemes/get_items` | Retrieve objects with optional filters, pagination, and requested fields |
| `POST` | `/api/schemes/create_items` | Create new objects (single or batch) with relationship management |
| `POST` | `/api/schemes/update_items` | Update existing objects with flexible filters and update types |
| `POST` | `/api/schemes/delete_items` | Delete objects based on filters (single or batch) |

> All endpoints require authentication (`login_required`).

---

### Example Request (Create Item)

```json
POST /api/schemes/create_items
{
  "model_name": "User",
  "requested_data": ["id"], 
  "object_values": {
    "username": "david",
    "email": "david@example.com",
    "roles": {
      "action": "link",
      "values": {
        "Role": {
          "query_filters": {"role": "Admin"},
          "link_type": "all_link"
        }
      }
    }
  },
  "reference": "User_david"
}

RESPONSE : 
{
  "status": 201,
  "message": "User_david created!",
  "body": [
    {
      "id": 12
    }
  ]
}

````

## Relationships Handling

### The backend allows dynamic relationship operations via API payloads:

	•	Link existing objects
	•	Unlink objects selectively or completely
	•	Create new related objects in batch or single
	•	Create through existing relationships (nested creation)

  ```json 

  "roles": {
  "action": "link",
  "values": {
    "Role": {
      "query_filters": {"role": "Admin"},
      "link_type": "all_link"
    }
  }
}

```

## Run Queries

The backend includes a dynamic query engine that allows you to fetch objects from the database using flexible filters, including nested relationships, batch conditions, and logical operators.
run queries is used by the schemes:

* /api/schemes/get_items
* /api/schemes/create_items
* /api/schemes/update_items
* /api/schemes/delete_items

Meaning you can take the following example for all types of manipulations in your calls.

### Example Request 

```json
{
  "model_name": "User",
  "requested_data": ["id", "username", "email", "roles.name"],
  "query_filters": {
    "status": {"operation": "==", "value": "active"},
    "age": {"operation": ">", "value": 25},
    "or-roles.name": {"operation": "==", "value": "Admin"}
  },
  "per_page": 10,
  "cursor": null
}
```

#### model_name
In here im quering in the Table call User ("model_name": "User" ).

#### reqeusted_data
And for each row I will get the direct values of: id, username, email ("requested_data":["id", ...]).

I will also get the value found in a relationship: role.name

#### query_filters
here im quering base on three columns "status", "age", "or-roles.name". the dictionary for each specifies the type of filtration and the target value ( all current query.filter_by operations are supported ).
the or- in or-roles.name is a way to say this is not "and" this is a "or" filter.


#### per_page
Restricts the total return values.
you can use cursor to implement next page queries.




### Response 

```json 
{
  "status": 200,
  "message": "Data adquired.",
  "body": [
    {
      "id": 12,
      "username": "david",
      "email": "david@example.com",
      "roles": [
        {"name": "Admin"},
        {"name": "Manager"}
      ]
    },
    {
      "id": 15,
      "username": "sarah",
      "email": "sarah@example.com",
      "roles": [
        {"name": "User"}
      ]
    }
    // Up to 10 items
  ]
}
```

#### body
We get a list of dicts back with the requested data.
Notice that the relationship return a list of dicts.



## Update Items

/update_items uses the same principles as /create_items, it calls the same function to fill object "def object_fill():"
the difference is that it requires a query_filters to find the items you want to modify, this is defined at the top level of the json.

Example: 

```json 
  {
  "model_name": "User",
  "reference": "User David",
  "object_values": {
    "username": "david_updated",
    "email": "david_updated@example.com",
    "roles": {
      "action": "link",
      "values": {
        "Role": {
          "query_filters": {"role": "Admin"},
          "link_type": "all_link"
        }
      }
    }
  },
  "query_filters": {
    "id": 12
  },
  "update_type": "first_match"
}
```
#### model_name:
The target table where we will find the object to be modified.

#### reference: 
Upon return you can use this to notify the user the action

#### object_values:
The values that will be modifies of the found object or objects. same as /create_item we can:
* modify simple columns
* link or unlink to relationships
* create other objects 
* update other objects 
* delete othe objects 

You also have dynamic options like, if I'm looking to link this object to a  relationship and is not found, then create the object in the relationship and link it.

### query_filters:
The filters you use to find the target object or objects. you can check /get_items for understanding how to use it.

### update_type:
Gives you the option to choose the number of updates you wish to perform upon query, in here we only want the first match to be updated.

### response
```json
{
  "status": 201,
  "message": "User david Updated!"
}
```




## Error Handling

#### The API responds consistently with:
	•	Validation errors (400)
	•	Database integrity errors (400)
	•	Data type errors (400)
	•	Operational/database errors (500)

Example response:
```json 
{
  "status": 400,
  "message": "[Database Integrity Error] The value 'Admin' for field 'role' already exists.",
  "server_message": "psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint"
}
```

### Setup Instructions

```bash 
# Clone repository
git clone https://github.com/Loorenz-David/Beyo_App_Flask

# Navigate to backend folder
cd BeyoPurchaseApp_v1.1/Back_End/Purchase_App

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run Flask server
export FLASK_APP=Purchase_App
export FLASK_ENV=development
flask run
```

### Set up

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Beyo_App_Flask.git

# Navigate to backend folder
cd BeyoPurchaseApp_v1.1/Back_End/Purchase_App

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt


```
### run.py
you can run the api from this file. notice that i had ssl_context set as i need it to use https, you can simply remove this ssl_context if you don't have .pem files

```python 
from Purchase_App import create_app
app = create_app()

if __name__ == '__main__':
    import os
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True,port=5001,
          #remove this parameter if you don't need https
            ssl_context=('certs/cert.pem','certs/key.pem')) 
    else:
        app.run(host='0.0.0.0',port=8080)
```


To use this api with a React front end you must add the http address of your front end to the env variable 'FRONT_END_URL'

Example: 

FRONT_END_URL='https://10.10.1.210:5173/'

You can test it using the React Front end that this api was made for, check the front end repository:

https://github.com/Loorenz-David/Beyo_App_React


### .env
It is advised to create a .env file with the following keys
* DATABASE_URL = 'some db url'
* SECRETE_KEY = 'temporary secrete key'
* FLASK_ENV = 'development'
FLASK_APP ='run.py'

I was using AWS for file and image uploading thus you can set up the following keys to use with the s3_routes.py file

* AWS_ACCESS_KEY_ID= ''
* AWS_SECRETE_ACCESS_KEY=''
* AWS_REGION = ''
* S3_BUCKET= ''





