from flask import Flask, render_template, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oghbs.db'
db = SQLAlchemy(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

curUserId = -1
checkInDate = datetime.now()
checkOutDate = datetime.now()
srt = '0'
foodId = '0'
availableOnly = '0'
roomId = 0

emptystatus = ""
for i in range(40):
    emptystatus+="0"

# user database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50))
    username = db.Column(db.String(20))
    password = db.Column(db.String(20))
    address = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    rollStd = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return '<Name %r>' % self.id


class GuestHouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(60))
    description = db.Column(db.String(60))


class Rooms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.Integer)
    type = db.Column(db.String(40))
    description = db.Column(db.String(60))  # Room type, no of beds
    status = db.Column(db.String(100))
    ghId = db.Column(db.Integer)
    pricePerDay = db.Column(db.Integer)
    occupancy = db.Column(db.Integer)
    ac = db.Column(db.Integer)


class FoodOptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pricePerDay = db.Column(db.Integer)
    type = db.Column(db.String(40))


class BookingQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookingIds = db.Column(db.String(40))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    roomId = db.Column(db.Integer)
    foodId = db.Column(db.Integer)
    checkInDate = db.Column(db.DateTime)
    checkOutDate = db.Column(db.DateTime)
    dateOfBooking = db.Column(db.DateTime)
    confirmation = db.Column(db.Integer)
    feedback = db.Column(db.String(100))

class Authentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    val = db.Column(db.Integer)

# prevent cached responses
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


@app.route('/loginDetails', methods=['POST'])
def getDetails():
    json = request.get_json()
    print(json)

    return jsonify(result="done")


@app.route('/', methods=["POST", "GET"])
def hello_world():
    if request.method == "POST":
        print(request.form['username'])
        user = User.query.filter_by(username=request.form['username']).first()
        print(request.form['password'])
        if user is not None and user.password == request.form['password']:
            global curUserId
            curUserId = user.id
            if user.id == 0:
                return admin()
            else:
                authstat = Authentication.query.filter_by(id=user.id).first()
                print(authstat.val)
                if authstat.val != 1:
                    return render_template('index.html', flag=authstat.val)
                return render_template('calender.html')
        else:
            return render_template('index.html', flag=1)
    return render_template('index.html', flag=3)


@app.route('/regForm', methods=["POST", "GET"])
def reg_form():
    if request.method == "POST":
        nextId = User.query.count()+1
        print(nextId)
        name = request.form['first_name'] + request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        gender = request.form['gender']
        age = request.form['age']
        address = request.form['address1']+", "+request.form['address2']+", City "+request.form['city']+", State "+request.form['state']
        rollStd = request.form['roll']
        user = User.query.filter_by(username=request.form['username']).first()
        user2 = User.query.filter_by(username=request.form['email']).first()
        if user is None and user2 is None:
            newUser = User(id=nextId, name=name, email=email, username=username, password=password, address=address, age=age, gender=gender, rollStd=rollStd)
            newRequest = Authentication(id=nextId, val=0)
            db.session.add(newRequest)
            db.session.commit()
        elif user2 is not None:
            return render_template('regform.html', flag=2)
        else:
            return render_template('regform.html', flag=0)
        # push to db
        try:
            db.session.add(newUser)
            db.session.commit()
            print("added successfully")
            return redirect('/')
        except:
            print("failed to add user to db")
    return render_template('regform.html', flag=1)

def checkAvailable(room):
    global checkInDate
    global checkOutDate
    temp = checkInDate.day - datetime.now().day
    checkInIndex = temp
    temp = checkOutDate.day - datetime.now().day
    checkOutIndex = temp
    if checkInIndex < 0 or checkOutIndex < 0:
        return False
    for i in room.status[checkInIndex:checkOutIndex+1]:
        if i == '1':
            return False
    return True


rooms = []
avail = []
days = []
urls = []
roomAvail = []

@app.route('/viewrooms', methods=["POST", "GET"])
def ViewRooms():
    global checkInDate
    global checkOutDate
    global srt
    global foodId
    global availableOnly
    global rooms
    global avail
    global days
    global urls
    global roomAvail

    if 'availableOnly' in request.form:
        print("checking availability")
        if request.form['availableOnly'] == '1':
            availableOnly = '1'
            rooms = [i for i in rooms if checkAvailable(i)]
        else:
            availableOnly = '0'
            rooms = Rooms.query.all()

    elif 'srt' in request.form:
        print("sorting")
        if request.form['srt'] == '0':
            srt = '0'
            rooms.sort(key=lambda x: x.pricePerDay)
        else:
            srt = '1'
            rooms.sort(key=lambda x: x.pricePerDay, reverse=True)
    if 'foodId' in request.form:
        print("addind food")

        for i in rooms:
            temp = Rooms.query.filter_by(id=i.id).first()
            i.pricePerDay = temp.pricePerDay
        foodId = request.form['foodId']

        idx = int(foodId)
        foodItem = FoodOptions.query.filter_by(id=idx).first()
        if foodItem is not None:
            for i in rooms:
                i.pricePerDay += foodItem.pricePerDay
    else:
        print("called")
        if 'checkintime' in request.form:
            checkindate = datetime.strptime(request.form['checkintime'], '%Y-%m-%d')
            checkoutdate = datetime.strptime(request.form['checkouttime'], '%Y-%m-%d')
            checkInDate = checkindate
            checkOutDate = checkoutdate
            if datetime.now() <= checkInDate <= checkOutDate and (checkOutDate-datetime.now()).days < 100:
                pass
            else:
                if curUserId == 0:
                    return render_template('adminCalendar.html', flag=0)
                return render_template('calender.html', flag=0)
        print("called")
        print(checkInDate)
        print(checkOutDate)
        if availableOnly == '1':
            rooms = [i for i in rooms if checkAvailable(i)]
        else:
            rooms = Rooms.query.all()
        if srt == '0':
            rooms.sort(key=lambda x: x.pricePerDay)
        else:
            rooms.sort(key=lambda x: x.pricePerDay, reverse=True)
        if foodId != '0':
            for i in rooms:
                temp = Rooms.query.filter_by(id=i.id).first()
                i.pricePerDay = temp.pricePerDay
            idx = int(foodId)
            foodItem = FoodOptions.query.filter_by(id=idx).first()
            if foodItem is not None:
                for i in rooms:
                    i.pricePerDay += foodItem.pricePerDay
        curdate = datetime.now()
        startDay = max(curdate, checkInDate-timedelta(days=3)).day - curdate.day
        startIdx = startDay
        startdate = max(curdate, checkInDate-timedelta(days=3))
        for i in range(7):
            temp = startdate + timedelta(days=i)
            days.append(temp.day)
        avail = []
        for room in rooms:
            temp = []
            urls.append("/room/"+str(room.id))
            print(room.status)
            for j in range(7):
                temp.append(int(room.status[startIdx+j]))
            avail.append(temp)

    print(avail)
    print(len(rooms))
    roomAvail = [0]*len(rooms)
    for i, room in enumerate(rooms):
        roomAvail[i] = 1 if checkAvailable(room) else 0
    print(roomAvail)
    return render_template('Booking.html', rooms=rooms, avail=avail, days=days, urls=urls, availableOnly=availableOnly, srt=srt, foodId=foodId, roomAvail=roomAvail)


@app.route('/room/<roomid>', methods=["POST", "GET"])
def room(roomid):
    global roomId
    print("room is")
    roomId = int(roomid)
    print(roomId)
    roomBook = Rooms.query.filter_by(id=roomId).first()
    foodBook = FoodOptions.query.filter_by(id=foodId).first()
    roomPrice = roomBook.pricePerDay*((checkOutDate.day-checkInDate.day)+1)
    foodPrice = 0
    if foodBook is not None:
        foodPrice = foodBook.pricePerDay*((checkOutDate.day-checkInDate.day)+1)

    payable = 0.2*(roomPrice+foodPrice)
    return render_template('Payment.html', roomPrice=roomPrice, foodPrice=foodPrice, payable=payable)


def BookingPrice(booking):
    food = FoodOptions.query.filter_by(id=booking.foodId).first()
    room = Rooms.query.filter_by(id=booking.roomId).first()
    noOfDays = ((booking.checkOutDate.day-booking.checkInDate.day)+1)
    price = room.pricePerDay*noOfDays
    if food is not None:
        price += food.pricePerDay*noOfDays
    return 0.2*price


@app.route('/calender', methods=["POST", "GET"])
def calender():
    return render_template('calender.html')


@app.route('/prevBookings', methods=["POST", "GET"])
def prevBookings():
    bookings = Booking.query.filter_by(userId=curUserId).all()
    curDate = datetime.now()
    for i in bookings:
        if curDate > i.checkInDate and i.confirmation == 1:
            i.confirmation = 4
            db.session.commit()
    user = User.query.filter_by(id=curUserId).first()
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in bookings]
    prices = [BookingPrice(i) for i in bookings]
    return render_template('prevBooking.html', bookings=bookings, user=user, rooms=rooms, prices=prices)


def changeRoom(roomId, checkInDate, checkOutDate, val):
    temp = checkInDate.day - datetime.now().day
    checkInIndex = max(0, temp)
    temp = checkOutDate.day - datetime.now().day
    checkOutIndex = temp
    room = Rooms.query.filter_by(id=roomId).first()
    print("start " + str(checkInDate))
    print("end " + str(checkOutDate))
    print("start " + str(checkInIndex))
    print("end " + str(checkOutIndex))
    newstatus = room.status[0:checkInIndex] + val*(checkOutIndex-checkInIndex+1) + room.status[checkOutIndex+1:]
    room.status = newstatus
    db.session.commit()


@app.route('/paymentDone', methods=["POST", "GET"])
def paymentDone():
    print("PaymentDone")
    nextId = Booking.query.count() + 1
    curRoom = Rooms.query.filter_by(id=roomId).first()
    conf = 1 if checkAvailable(curRoom) else 0
    roomQueue = BookingQueue.query.filter_by(id=roomId).first()
    if checkAvailable(curRoom):
        changeRoom(roomId, checkInDate, checkOutDate, '1')
        print(curRoom.status)
    else:
        roomQueue = BookingQueue.query.filter_by(id=roomId).first()
        if roomQueue is None:
            print("first")
            newId = str(nextId)
            newId = newId.rjust(4, '0')
            tempStatus = newId
            tempStatus = tempStatus.ljust(40, '0')
            temp = BookingQueue(id=roomId, bookingIds=tempStatus)
            print(tempStatus)
            db.session.add(temp)
            db.session.commit()
        else:
            print("second")
            here = 36
            newId = str(nextId)
            newId = newId.rjust(4, '0')
            print("reserving")
            print(roomQueue)
            print(roomQueue.bookingIds)
            for idx in range(0, 40, 4):
                checker = roomQueue.bookingIds[idx:idx+4]
                print(checker)
                if int(checker) == 0:
                    here = idx
                    break
            newstatus = roomQueue.bookingIds[:here] + newId + (roomQueue.bookingIds[here+4:] if here+4 < 39 else "")
            roomQueue.bookingIds = newstatus
            db.session.commit()

    newBooking = Booking(id=nextId, userId=curUserId, roomId=roomId, foodId=foodId, checkInDate=checkInDate, checkOutDate=checkOutDate, dateOfBooking=datetime.now().date(), confirmation=conf, feedback="")
    try:
        db.session.add(newBooking)
        db.session.commit()
        print("Booking added successfully")
    except:
        print("failed to add Booking to db")

    return prevBookings()

def BookAvailable(bookingId):
    booking = Booking.query.filter_by(id=bookingId).first()
    if booking is None:
        return False
    checkInDate = booking.checkInDate
    checkOutDate = booking.checkOutDate
    room = Rooms.query.filter_by(id=booking.roomId).first()
    temp = checkInDate.day - datetime.now().day
    checkInIndex = temp
    temp = checkOutDate.day - datetime.now().day
    checkOutIndex = temp
    if checkInIndex < 0 or checkOutIndex < 0:
        return False
    for i in room.status[checkInIndex:checkOutIndex+1]:
        if i == '1':
            return False
    booking.confirmation = 1
    db.session.commit()
    changeRoom(booking.roomId, checkInDate, checkOutDate, '1')
    return True


@app.route('/cancelBooking<bookingId>', methods=["POST", "GET"])
def cancelBooking(bookingId):
    print("Cancelling")
    booking = Booking.query.filter_by(id=bookingId).first()
    roomId = booking.roomId
    queue = BookingQueue.query.filter_by(id=roomId).first()
    if booking.confirmation == 0:
        roomQueue = BookingQueue.query.filter_by(id=roomId).first()
        tempIds = ""
        for idx in range(0, 40, 4):
            checker = roomQueue.bookingIds[idx:idx + 4]
            if int(checker) != booking.id:
                tempIds += checker
        tempIds = tempIds.ljust(40, '0')
        roomQueue.bookingIds = tempIds
        db.session.commit()
    else:
        changeRoom(roomId, booking.checkInDate, booking.checkOutDate, '0')
        roomQueue = BookingQueue.query.filter_by(id=roomId).first()
        if roomQueue is not None:
            tempiDs = ""
            for idx in range(0, 40, 4):
                checker = roomQueue.bookingIds[idx:idx + 4]
                if BookAvailable(int(checker)):
                    pass
                else:
                    tempiDs += checker
            tempiDs = tempiDs.ljust(40, '0')
            roomQueue.bookingIds = tempiDs
            db.session.commit()

    booking.confirmation = 3
    db.session.commit()
    if curUserId == 0:
        return adminPrevBooking()
    return prevBookings()


@app.route('/admin', methods=["POST", "GET"])
def admin():
    allReq = Authentication.query.filter_by(val=0)
    users = []
    for req in allReq:
        users.append(User.query.filter_by(id=req.id).first())
    return render_template('admin.html', users=users)


@app.route('/adminCalendar', methods=["POST", "GET"])
def adminCalender():
    return render_template('adminCalendar.html')


@app.route('/adminPrevBooking', methods=["POST", "GET"])
def adminPrevBooking():
    bookings = Booking.query.all()
    user = [User.query.filter_by(id=i.userId).first() for i in bookings]
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in bookings]
    prices = [BookingPrice(i) for i in bookings]
    return render_template('adminPrevBooking.html', bookings=bookings, user=user, rooms=rooms, prices=prices)


@app.route('/authorize/<userId>/<desc>', methods=["POST", "GET"])
def authorize(userId, desc):
    userId = int(userId)
    desc = int(desc)
    userVal = Authentication.query.filter_by(id=userId).first()
    userVal.val = desc
    db.session.commit()
    return admin()


@app.route('/feedback/<bookingId>', methods=["POST", "GET"])
def feedback(bookingId):
    return render_template('feedback.html', bookingId=bookingId)

@app.route('/setfeedback/<bookingId>', methods=["POST", "GET"])
def setfeedback(bookingId):
    text = request.form['text']
    booking = Booking.query.filter_by(id=bookingId).first()
    booking.feedback = text
    booking.confirmation = 5
    db.session.commit()
    return prevBookings()

if __name__ == '__main__':
    app.run()
