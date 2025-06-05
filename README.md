Fitness Booking Api

The Fitness Studio Booking API is a RESTful backend service designed to manage:

1. Fitness class scheduling
2. User bookings
3. Slot availability tracking
4.Automated class status updates

1. Fitness class scheduling
Create, update, and cancel fitness classes
track available slots
Automatic status updates (upcoming → completed)

2.Booking System
Users can book classes 
Prevents double bookings for the same class
Limits users to 3 upcoming bookings at a time
Supports cancellations

3. Automated Background Jobs
Slot Release Service
Runs every 15 minutes
Automatically releases slots when classes end
Runs every 5 minutes (6 AM–10 PM)

4. Data Integrity & Validation
Class time validation (end time > start time)
Email format verification
Slot availability checks before booking
Case-insensitive email queries to avoid duplicates

API Endpoints:
Endpoint	Method	Description	Parameters

1.Create Class:
POST
http://localhost:8000/bookings
Body:
{
    "class_id": 3,
    "client_name": "naina4 jaiswal",
    "client_email": "naina4J@gmail.com"
}
Response:
{
    "class_id": 3,
    "client_name": "naina4 jaiswal",
    "client_email": "naina4j@gmail.com",
    "id": 9,
    "booking_time": "2025-06-05T14:53:05.725172",
    "checked_in": false,
    "is_cancelled": false,
    "fitness_class": {
        "name": "Pilates Class",
        "instructor": "Alice Johnson",
        "start_time": "2025-06-08T14:57:53.074905",
        "end_time": "2025-06-08T15:57:53.074909",
        "capacity": 10,
        "timezone": "UTC",
        "id": 3,
        "available_slots": 5
    }
}

2. Get Booking details by email
GET
http://localhost:8000/bookings?email=nainaJ@gmail.com
Response
 {
        "class_id": 3,
        "client_name": "naina jaiswal",
        "client_email": "nainaj@gmail.com",
        "id": 6,
        "booking_time": "2025-06-05T12:51:09.325828",
        "checked_in": false,
        "is_cancelled": false,
        "fitness_class": {
            "name": "Pilates Class",
            "instructor": "Alice Johnson",
            "start_time": "2025-06-08T14:57:53.074905",
            "end_time": "2025-06-08T15:57:53.074909",
            "capacity": 10,
            "timezone": "UTC",
            "id": 3,
            "available_slots": 8
        }
    }
3. Get All Class details
GET
http://localhost:8000/classes
Response:
{
        "name": "Yoga Class",
        "instructor": "john Doe",
        "start_time": "2025-06-06T14:57:53.074609",
        "end_time": "2025-06-06T15:57:53.074628",
        "capacity": 20,
        "timezone": "UTC",
        "id": 1,
        "available_slots": 0
    },
    {
        "name": "Zumba Class",
        "instructor": "Jane Smith",
        "start_time": "2025-06-07T14:57:53.074825",
        "end_time": "2025-06-07T15:57:53.074830",
        "capacity": 15,
        "timezone": "UTC",
        "id": 2,
        "available_slots": 0
    },
    {
        "name": "Pilates Class",
        "instructor": "Alice Johnson",
        "start_time": "2025-06-08T14:57:53.074905",
        "end_time": "2025-06-08T15:57:53.074909",
        "capacity": 10,
        "timezone": "UTC",
        "id": 3,
        "available_slots": 8
    },
    {
        "name": "Hiit Class",
        "instructor": "Bob Brown",
        "start_time": "2025-06-09T14:57:53.074963",
        "end_time": "2025-06-09T15:57:53.074967",
        "capacity": 25,
        "timezone": "UTC",
        "id": 4,
        "available_slots": 25
    }
    
4. Cancel class api
    POST
    http://localhost:8000/classes/{class_id}/cancel
    {
    "message": "Class cancelled successfully"
}
5. Check in APi 
POST
http://localhost:8000/classes/{class_id}/check-in/{booking_id}
Response:
{
    "message": "Attendee checked in successfully"
}

 Error Handling

Code	        Message	
400	          No available slots	
400	          Class has already started	
404	          Class not found	
409	          Already booked this class	

Setup Instructions:

git clone https://github.com/Sadaf244/fitness_booking_api.git
cd booking_app
cd api
python -m venv venv
source venv/bin/activate  
venv\Scripts\activate    
pip install -r requirements.txt
uvicorn main:app --reload


    
