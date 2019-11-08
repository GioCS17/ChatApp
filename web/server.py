from flask import Flask,render_template,jsonify, request, session, Response, redirect,url_for, send_file
from io import BytesIO
from database import connector 
from model import entities
from datetime import datetime
import json
import time
import base64
from flask_socketio import SocketIO,send,emit,join_room
import eventlet 


db = connector.Manager()
engine = db.createEngine()

app = Flask(__name__)


#Initialize socketio
socketio=SocketIO(app,manage_session=False)

users_total={}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<content>')
def static_content(content):
    return render_template(content)

@app.route('/registerUser', methods = ['POST'])
def registerUser():
    print('Entroa register user')
    c = request.form
    photo=request.files['fileImage']
    user = entities.User(
        name=c['name'],
        fullname=c['fullname'],
        username=c['username'],
        password=c['password'],
        photoName=photo.filename,
        photoData=photo.read()
    )
    session = db.getSession(engine)
    users = session.query(entities.User).filter(entities.User.username == user.username)
    msg=""
    for u in users:
        msg="Usuario ya registrado"
        return render_template('register.html',msg=msg)
    session.add(user)
    session.commit()
    return render_template('index.html')

@app.route('/download')
def download():
    db_session=db.getSession(engine)
    user = db_session.query(entities.User).filter(entities.User.username=='mbrandon').one()
    return send_file(BytesIO(user.photoData),attachment_filename=user.photoName,as_attachment=True)
    
@app.route('/profile')
def profile():
    db_session=db.getSession(engine)
    username=session['logged_username']
    user = db_session.query(entities.User
        ).filter(entities.User.username==username
        ).one()
    image=base64.b64encode(user.photoData)
    image=image.decode('utf-8')
    return render_template('profile.html',user=user,imgBytes=image)

@app.route('/friends')
def friends():
    db_session = db.getSession(engine)
    id_user=session['logged_user']
    conts = db_session.query(entities.Contacts).filter(entities.Contacts.user_id == id_user)

    contacts=[]
    for cont in conts:
        c = db_session.query(entities.User).filter(entities.User.id == cont.contact_id).first()
        image=base64.b64encode(c.photoData)
        image=image.decode('utf-8')
        print(type(image))
        print(len(image))
        contacts.append([c,image])
    return render_template('friends.html',contacts=contacts)

@app.route('/addContact',methods=['POST'])
def addContact():
    db_session = db.getSession(engine)
    c = request.form

    username_cont=c['username']
    username_user=session['logged_username'] 

    #Valido si ingresa su usuario como contacto
    if username_cont==username_user:
        print('Usuario ingresado es el suyo')
        return redirect(url_for('friends'))

    #Valido si ingresa un usuario en db
    user_cont = db_session.query(entities.User).filter(entities.User.username== username_cont).first()
    if not user_cont:
        print('Usuario no existe')
        return redirect(url_for('friends'))

    id_user=session['logged_user']

    #Valido si es un contacto ya registrado
    cont_ver = db_session.query(entities.Contacts).filter(
        entities.Contacts.user_id== id_user).filter(
            entities.Contacts.contact_id==user_cont.id).first()
    
    if cont_ver:
        print('Usuario ya es contact')
        return redirect(url_for('friends'))

    cont = entities.Contacts(
        user_id=id_user,
        contact_id=user_cont.id
    )
    db_session.add(cont)
    db_session.commit()
    return redirect(url_for('friends'))


@app.route('/setContactID', methods = ['POST'])
def setContactID():
    contact_id=request.json
    print("seteo contact_id ",contact_id,type(contact_id))
    session['contact_id']=contact_id
    db_session=db.getSession(engine)
    user_cont = db_session.query(entities.User).filter(entities.User.id == contact_id).first()
    session['contact_username']=user_cont.username
    datamsg=get_messages_user(contact_id,session['logged_user'])
    datamsgJson=[]
    for msg in datamsg:
        datamsgJson.append({"user_from": msg.user_from_id, "user_to": msg.user_to_id,"content":msg.content})
    datamsg=json.dumps(datamsgJson)
    return jsonify(datamsg)

def get_messages_user(user_from_id, user_to_id ):
    db_session = db.getSession(engine)
    messages_send = db_session.query(entities.Message).filter(
        entities.Message.user_from_id == user_from_id).filter(
        entities.Message.user_to_id == user_to_id
    )
    messages_recieved = db_session.query(entities.Message).filter(
        entities.Message.user_from_id == user_to_id).filter(
        entities.Message.user_to_id == user_from_id
    )
    data = []
    for message in messages_send:
        data.append(message)
    for message in messages_recieved:
        data.append(message)
    data=sorted(data, key=lambda x:x.sent_on)
    return data

@socketio.on('message')
def message(data):
    try:
        print('mensage llego',data['msg'])
        message=data['msg']
        print('Enviado a ',session['contact_id'])

        db_session = db.getSession(engine)
        msg = entities.Message(
            content=message,
            sent_on=datetime.today(),
            user_from_id=session['logged_user'],
            user_to_id=session['contact_id']
        )
        db_session = db.getSession(engine)
        db_session.add(msg)
        db_session.commit()
        room=session['contact_id']
        #print("Enviadose mensage a usuario con id :::"+room,type(room))
        #//global users_total
        #print(users_total)
        #emit('privateMessage', {'message':message},room=users_total[int(room)])
    except Exception as e:
        print("Error en enviar mensaje")
        print(e)

@app.route('/users/<id>', methods = ['GET'])
def get_user(id):
    for user in users:
        js = json.dumps(user, cls=connector.AlchemyEncoder)
        return  Response(js, status=200, mimetype='application/json')

    message = { 'status': 404, 'message': 'Not Found'}
    return Response(message, status=404, mimetype='application/json')


def getUser(id):
    session = db.getSession(engine)
    user = session.query(entities.User).filter(entities.User.id == id).first()
    return user

@app.route('/users/<id>', methods = ['DELETE'])
def delete_user(id):
    session = db.getSession(engine)
    user = session.query(entities.User).filter(entities.User.id == id).one()
    session.delete(user)
    session.commit()
    return "Deleted User"

@app.route('/messages/<id>', methods = ['GET'])
def get_message(id):
    db_session = db.getSession(engine)
    messages = db_session.query(entities.Message).filter(entities.Message.id == id)
    for message in messages:
        js = json.dumps(message, cls=connector.AlchemyEncoder)
        return Response(js, status=200, mimetype='application/json')

    message = {'status': 404, 'message': 'Not Found'}
    return Response(message, status=404, mimetype='application/json')

@app.route('/messages', methods = ['GET'])
def messages():
    sessionc = db.getSession(engine)
    dbResponse = sessionc.query(entities.Message)
    data = dbResponse[:]
    dataf=[]
    print(type(data))
    for i in data:
        print(i.user_from_id,getUser(i.user_from_id))
    return render_template('messages.html',messages=data)

@app.route('/updateMessage/<id>', methods = ['POST'])
def updateMessage(id):
    session = db.getSession(engine)
    msg= session.query(entities.Message).filter(entities.Message.id == id).first()
    c = request.form
    for key in c.keys():
        setattr(msg, key, c[key])
    session.add(msg)
    session.commit()
    return redirect(url_for('messages'))

@app.route('/messages', methods = ['PUT'])
def update_message():
    session = db.getSession(engine)
    id = request.form['key']
    message = session.query(entities.Message).filter(entities.Message.id == id).first()
    c = json.loads(request.form['values'])
    for key in c.keys():
        setattr(message, key, c[key])
    session.add(message)
    session.commit()
    return 'Updated Message'

@app.route('/messageDelete/<id>')
def delete_message(id):
    session = db.getSession(engine)
    message = session.query(entities.Message).filter(entities.Message.id == id).one()
    session.delete(message)
    session.commit()
    return redirect(url_for('messages'))

@socketio.on('addUserToRoom')
def addUserToRoom(data):
    db_session=db.getSession(engine)
    user = db_session.query(entities.User).filter(entities.User.username==data['username']).one()
    global users_total
    users_total[user.id]=request.sid
    print('Id user registrado en room ',user.id,type(user.id))
    print('Con key ',request.sid)
    print("Users total ",users_total)
    join_room(request.sid)

@app.route('/authenticate', methods = ['POST'])
def authenticate():
    #Get data form request
    message = request.form
    username = message['username']
    password = message['password']

    # Look in database
    db_session = db.getSession(engine)
    print(username,password)
    msg=""
    try:
        user = db_session.query(entities.User
            ).filter(entities.User.username==username
            ).filter(entities.User.password==password
            ).one()
        image=base64.b64encode(user.photoData)
        image=image.decode('utf-8')
        session['logged_user'] = user.id
        session['logged_username'] = user.username
        return render_template('profile.html',user=user,imgBytes=image)
    except Exception as e:
        #message = {'message':'Unauthorized'}
        print('bad')
        print(e)
        msg="Usuario no registrado"
        return render_template('login.html',msg=msg)

@app.route('/current', methods = ['GET'])
def current_user():
    db_session = db.getSession(engine)
    user = db_session.query(entities.User).filter(entities.User.id == session['logged_user']).first()
    return Response(json.dumps(user,cls=connector.AlchemyEncoder),mimetype='application/json')

@app.route('/logout', methods = ['GET'])
def logout():
    session.clear()
    return render_template('login.html')

#API de GRUPOS
#1. CREATE
@app.route('/groups', methods = ['POST'])
def create_group():
    c = json.loads(request.data)
    group = entities.Group(name=c['name'])
    session_db = db.getSession(engine)
    session_db.add(group)
    session_db.commit()
    return 'Created Group'

#2. READ
@app.route('/groups/<id>', methods = ['GET'])
def read_group(id):
    session_db = db.getSession(engine)
    group = session_db.query(entities.Group).filter(
        entities.Group.id == id).first()
    data = json.dumps(group, cls=connector.AlchemyEncoder)
    return  Response(data, status=200, mimetype='application/json')

@app.route('/groups', methods = ['GET'])
def get_all_groups():
    session_db = db.getSession(engine)
    dbResponse = session_db.query(entities.Group)
    data = dbResponse[:]
    return Response(json.dumps(data,
        cls=connector.AlchemyEncoder), mimetype='application/json')

# UPDATE
@app.route('/groups/<id>', methods = ['PUT'])
def update_group(id):
    session_db = db.getSession(engine)
    group = session_db.query(entities.Group).filter(entities.Group.id == id).first()
    c = json.loads(request.data)

    for key in c.keys():
        setattr(group, key, c[key])
    session.add(group)
    session.commit()
    return 'Updated GROUP'

# DELETE
@app.route('/groups/<id>', methods = ['DELETE'])
def delete_group(id):
    session_db = db.getSession(engine)
    user = session_db.query(entities.Group).filter(entities.Group.id == id).one()
    session_db.delete(user)
    session_db.commit()
    return "Deleted User"

@app.route('/users',methods=['GET'])
def users():
    session = db.getSession(engine)
    dbResponse = session.query(entities.User)
    users= dbResponse[:]
    return render_template('users.html',users=users)

@app.route('/addUser', methods = ['POST'])
def addUser():
    c = request.form
    user = entities.User(
        username=c['username'],
        name=c['name'],
        fullname=c['fullname'],
        password=c['password']
    )
    session = db.getSession(engine)
    session.add(user)
    session.commit()
    return redirect(url_for('users'))

@app.route('/getUpdateUser/<id>', methods = ['GET'])
def getUpdateUserContact(id):
    session = db.getSession(engine)
    user = session.query(entities.User).filter(entities.User.id == id).first()
    return render_template('updateUser.html',user=user)

@app.route('/updateUser/<id>', methods = ['POST'])
def updateUser(id):
    session = db.getSession(engine)
    user = session.query(entities.User).filter(entities.User.id == id).first()
    c = request.form

    for key in c.keys():
        setattr(user, key, c[key])
    session.add(user)
    session.commit()
    return redirect(url_for('users'))

@app.route('/deleteUser/<id>')
def deleteUser(id):
    session = db.getSession(engine)
    user = session.query(entities.User).filter(entities.User.id == id).one()
    session.delete(user)
    session.commit()
    return redirect(url_for('users'))


@app.route('/mostrarChat')
def mostrarChat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.secret_key = ".."
    #app.run(debug=True,port=8080, threaded=True, host=('127.0.0.1'))
    app.run(debug=True,threaded=True,port=80,use_reloader=True)
    #socketio.run(app,debug=True,port=8000)
