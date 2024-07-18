# from falkordb import FalkorDB
#
# # Connect to FalkorDB
# db = FalkorDB(host="r-6jissuruar.instance-f8445ltcz.hc-dx5io0svq.asia-south1.gcp.f2e0a955bb84.cloud",
#               port=51965, username="falkordbTest", password='password')
#
# # Create the 'MotoGP' graph
# g = db.select_graph('PassBy')
#
# # Create a vertex
# # g.query("""CREATE
# #           (:Person {name:'Maoz Daniel'})-[:livesIn]->(:City {name:'Zofim'}),
# #           (:Person {name:'Arad Daniel'})-[:sisterof]->(:Person {name:'Maoz Daniel'}),
# #           (:Person {name:'Noam Solow'})-[:isFriendWith]->(:Person {name:'Arad Daniel'}),
# #           (:Person {name:'Eitan Klein'})-[:isFriendWith]->(:Person {name:'Maoz Daniel'}),
# #           (:Person {name:'Maoz Daniel'})-[:isFriendWith]->(:Person {name:'Noam Solow'}),
# #           (:Person {name:'Noam Solow'})-[:Has]->(:Title {name:'criminal record'})""")
#
#
# resCriminal = g.query("""
#                     MATCH (p:Person)-[:isFriendWith*1..4]->(criminal:Person)-[:Has]->(:Title {name:'criminal record'})
#                     RETURN p.name
#                 """)
#
# for row in resCriminal.result_set:
#     print(row[0])

from falkordb import FalkorDB

# Connect to FalkorDB (using the port from the image)
db = FalkorDB(host='r-6jissuruar.instance-nqqhe0h35.hc-v8noonp0c.europe-west1.gcp.f2e0a955bb84.cloud',
              port=64955, username='falkordb', password='N0ams0l0w')

# Select the appropriate graph
g = db.select_graph('PassBY1')

# Sample data for cars and people
cars_data = [
    {"license_plate": "01234576", "car_type": "Sedan", "color": "Red", "pass_count": 3, "owner_id": 1, "stolen": False,
     "license_plate_type": "Yellow"},
    {"license_plate": "6922258", "car_type": "SUV", "color": "Blue", "pass_count": 5, "owner_id": 2, "stolen": False,
     "license_plate_type": "Yellow"},
    {"license_plate": "012345787", "car_type": "Truck", "color": "Green", "pass_count": 2, "owner_id": 3,
     "stolen": False, "license_plate_type": "Green"},
    {"license_plate": "6123430", "car_type": "Coupe", "color": "Black", "pass_count": 4, "owner_id": 4, "stolen": False,
     "license_plate_type": "Yellow"},
    {"license_plate": "61234308", "car_type": "Hatchback", "color": "White", "pass_count": 1, "owner_id": 5,
     "stolen": False, "license_plate_type": "White"}
]

people_data = [
    {"id": 1, "name": "Alice", "age": 30, "gender": "Female", "address": "123 Main St",
     "family_members": ["Bob", "Charlie"], "criminal_record": 3, "passes_border_count": 2},
    {"id": 2, "name": "Bob", "age": 32, "gender": "Male", "address": "456 Elm St", "family_members": ["Alice", "David"],
     "criminal_record": 2, "passes_border_count": 3},
    {"id": 3, "name": "Charlie", "age": 28, "gender": "Male", "address": "789 Oak St",
     "family_members": ["Alice", "Eve"], "criminal_record": 1, "passes_border_count": 1},
    {"id": 4, "name": "David", "age": 35, "gender": "Male", "address": "101 Pine St",
     "family_members": ["Bob", "Frank"], "criminal_record": 4, "passes_border_count": 4},
    {"id": 5, "name": "Eve", "age": 27, "gender": "Female", "address": "202 Cedar St",
     "family_members": ["Charlie", "Grace"], "criminal_record": 5, "passes_border_count": 0}
]

# Checkpoint (Border) data
checkpoint_data = {"name": "Border"}

# Create Cypher queries for inserting nodes and relationships
car_queries = []
person_queries = []

# Create Person nodes
for person in people_data:
    person_queries.append(
        f"CREATE (:Person {{id: {person['id']}, name: '{person['name']}', "
        f"age: {person['age']}, gender: '{person['gender']}', "
        f"address: '{person['address']}', family_members: {person['family_members']}, "
        f"criminal_record: {person['criminal_record']}, passes_border_count: {person['passes_border_count']}}})"
    )

# Create Checkpoint (Border) node
checkpoint_query = f"CREATE (:Checkpoint {{name: '{checkpoint_data['name']}'}})"

# Execute all queries to create persons and checkpoint
g.query(checkpoint_query)
for query in person_queries:
    g.query(query)

# Create Car nodes with relationships
for car in cars_data:
    # First create the Car node
    car_query = f"""
    CREATE (:Car {{license_plate: '{car['license_plate']}', car_type: '{car['car_type']}', 
                   color: '{car['color']}', pass_count: {car['pass_count']}, 
                   stolen: {car['stolen']}, license_plate_type: '{car['license_plate_type']}'}})
    """
    g.query(car_query)

    # Then establish the relationship with its owner
    owner_id = car['owner_id']
    relation_query = f"""
    MATCH (car:Car {{license_plate: '{car['license_plate']}'}})
    MATCH (owner:Person {{id: {owner_id}}})
    MERGE (owner)-[:isOwnerOf]->(car)
    """
    g.query(relation_query)

print("Nodes and relationships created successfully.")


def query_car_details(license_plate):
    # Cypher query to retrieve all details about the car and its owner
    query_car_details = f"""
    MATCH (c:Car {{license_plate: '{license_plate}'}})
    OPTIONAL MATCH (c)<-[:isOwnerOf]-(owner:Person)
    RETURN c.license_plate, c.car_type, c.color, c.pass_count, c.stolen, 
           c.license_plate_type,
           owner.name AS OwnerName,
           owner.family_members AS OwnerFamilyMembers,
           owner.criminal_record AS OwnerCriminalRecord,
           owner.age AS OwnerAge,
           owner.gender AS OwnerGender,
           owner.passes_border_count AS OwnerPassesBorderCount
    """

    # Execute the query and fetch the result
    res_car_details = g.query(query_car_details)
    stringans = ""
    ans = 0

    # Process the result
    if res_car_details.result_set:
        car_details = res_car_details.result_set[0]

        # Build the dict for detailed output

        car_details_dict = {
            "License_Plate": car_details[0],
            "Car_Type": car_details[1],
            "Color": car_details[2],
            "Pass_Count": car_details[3],
            "Stolen": "Yes" if car_details[4] else "No",
            "License_Plate_Type": car_details[5],
            "Owner_Name": car_details[6],
            "Owner_Family_Members": car_details[7],
            "Owner_Criminal_Record": car_details[8]
        }

        # Calculate the 'ans' score based on car details
        if car_details[3] <= 10:  # 10 or less passes
            ans += 5
            car_details_dict["Pass_Count"] = (car_details[3], 5)
        elif car_details[3] <= 5:  # 5 or less passes
            ans += 10
            car_details_dict["Pass_Count"] = (car_details[3], 10)
        if car_details[4]:  # is stolen
            ans += 65
            car_details_dict["Stolen"] = (car_details[4], 65)
        if car_details[5]:  # license_plate_type
            if car_details[5] == "Green":  # Green license plate
                ans += 25
                car_details_dict["License_Plate_Type"] = (car_details[5], 25)
            elif car_details[5] == "White":  # White license plate
                ans -= 10
                car_details_dict["License_Plate_Type"] = (car_details[5], -10)
        if car_details[8]:  # Criminal record
            ans += car_details[8] * 10
            car_details_dict["Owner_Criminal_Record"] = (car_details[8], car_details[8] * 10)
        """
        if car_details[9] is not None and 15 <= car_details[9] <= 30:  # 15-30 years old
            ans += 10
        if car_details[10] == "Male":  # gender
            ans += 10
        """

    else:
        car_details_dict = {"License_Plate": ('undefined', 0),
                            "Car_Type": ('undefined', 0),
                            "Color": ('undefined', 0),
                            "Pass_Count": ('undefined', 0),
                            "Stolen": ('undefined', 0),
                            "License_Plate_Type": ('undefined', 0),
                            "Owner_Name": ('undefined', 0),
                            "Owner_Family_Members": ('undefined', 0),
                            "Owner_Criminal_Record": ('undefined', 0)
                            }
        ans = 80

    return ans, car_details_dict
