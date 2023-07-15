from flask import *
import mysql.connector
from flask_session import Session
from key import *
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import *
import os


app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

mysql = mysql.connector.connect(host="localhost", user="root", password="root", database="feemanagement")

@app.route('/')
def title():
    return render_template('title.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count:
            session['user']=username
            return redirect(url_for('fees'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        username = request.form['username']
        # email=request.form['email']
        password = request.form['password']
        cursor = mysql.cursor(buffered=True)
        cursor.execute('SELECT COUNT(*) FROM admin WHERE name=%s AND password=%s', [username, password])
        count = cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            session['admin'] = username
            flash('Only Admin can login here')
            return redirect(url_for('add_course'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('adminlogin'))

    return render_template('adminlogin.html')
    
@app.route('/adminregister', methods=['GET', 'POST'])
def adminregister():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.cursor()
        cursor.execute('insert into admin values(%s,%s,%s)',[username,email,password])
        mysql.commit()
        cursor.close()
        return redirect(url_for('adminlogin'))
    return render_template('adminregister.html')


@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        age=request.form['age']
        gender=request.form['gender']
        address=request.form['address']
        mobile=request.form['mobile']
        password=request.form['password']
        email=request.form['email']
        cursor=mysql.cursor()
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'age':age,'mobile':mobile,'password':password,'email':email,'gender':gender,'address':address}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mysql.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users (USERNAME,AGE,MOBILE,EMAIL,PASSWORD,GENDER,ADDRESS) values(%s,%s,%s,%s,%s,%s,%s)',[data['username'],data['age'],data['mobile'],data['email'],data['password'],data['gender'],data['address']])
            mysql.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
        

@app.route('/forgot',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.cursor(buffered=True)
        cursor.execute('select count(*) from users where email=%s',[email])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mysql.cursor(buffered=True)
            cursor.execute('SELECT email from users where email=%s',[email])
            status=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[newpassword,email])
                mysql.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('User Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/adminlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        flash(' Admin Successfully logged out')        
        return redirect(url_for('adminlogin'))
    else:
        return redirect(url_for('adminlogin'))

@app.route('/view_course',methods=['GET','POST'])
def view_course():
    if session.get('user'):
        cur = mysql.cursor()
        cur.execute("SELECT * FROM courses")
        courses = cur.fetchall()
        cur.close()
    else:
        return redirect(url_for('login'))
    return render_template('home.html', courses=courses)

@app.route('/adminhome',methods=['GET','POST'])
def adminhome():
    if session.get('admin'):
        cur = mysql.cursor()
        cur.execute("SELECT * FROM courses")
        courses = cur.fetchall()
        cur.close()
    else:
        return redirect(url_for('adminlogin'))
    return render_template('adminhome.html', courses=courses)

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if session.get('admin'):
        if request.method == 'POST':
            course_name = request.form['course_name']
            course_fee = request.form['course_fee']
            cur = mysql.cursor()
            cur.execute("INSERT INTO courses (name, fee) VALUES (%s, %s)", (course_name, course_fee))
            mysql.commit()
            cur.close()
            return redirect('/add_course')
    else:
        return redirect(url_for('adminlogin'))
    return render_template('add_course.html')
@app.route('/fees', methods=['GET'])
def fees():
    if session.get('user'):
        course_id = request.args.get('course_id')
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM courses WHERE id = %s", [course_id])
        course = cursor.fetchone()
        # print(course)
        cursor.close()
        if course:
            return render_template('fees.html', course=course)
        else:
            # flash('Course not found')
            return redirect(url_for('view_course'))
    else:
        return redirect(url_for('login'))


@app.route('/submit', methods=['GET','POST'])
def submit():
    if session.get('user'):    
        if request.method == 'POST':
            student_name = request.form['student_name']
            course_id = request.form['course_id']
            amount_paid = request.form['amount_paid']
            cursor = mysql.cursor()
            cursor.execute("SELECT COUNT(*) FROM students WHERE name = %s AND course_id = %s", (student_name, course_id))
            payment_count = cursor.fetchone()[0]
            print(payment_count)
            if payment_count > 0:
                cursor.execute("select amount_paid,total_amount from students WHERE name = %s AND course_id = %s",( student_name, course_id))
                result = cursor.fetchone()
                if result is not None:
                    amount = result[0]
                    total_amount = result[1]
                    cursor.close()
                    print("Amount Paid:", amount)
                    print("Total Amount:", total_amount)
                    if int(amount) == total_amount:
                        flash("You have already paid for this course.")
                        return redirect(url_for('view_course'))
                    if int(amount) < total_amount:
                        remaining_amount = total_amount - int(amount)
                        print('remaining_amount', remaining_amount)
                        print(amount_paid)
                        a = remaining_amount - int(amount_paid) 
                        if a < 0:
                            flash(f"you need to pay {remaining_amount} or can pay less than that amount")
                            return redirect(url_for('view_course'))
                        else:
                            print('a', a)
                            b = int(amount_paid) + int(amount) 
                            print('b', b)
                            cursor = mysql.cursor()
                            cursor.execute("UPDATE students SET remaining_amount = %s  WHERE course_id = %s", [a,course_id])
                            cursor.execute("UPDATE students SET amount_paid = %s  WHERE course_id = %s", [b,course_id])
                            mysql.commit()
                            cursor.close()
                            return render_template('pay.html')
                else:
                    print("No data found.")
                    flash("No data found.")
                    return redirect(url_for('view_course'))
            else:
                cursor = mysql.cursor()
                cursor.execute("select fee from courses WHERE id = %s", [course_id])
                fee = cursor.fetchone()
                fee=int(fee[0])
                cursor.close()
                if int(amount_paid):
                    remaining_amount = fee - int(amount_paid)
                    cursor = mysql.cursor()
                    cursor.execute("INSERT INTO students (name, course_id, amount_paid, feestatus,remaining_amount,total_amount) VALUES (%s, %s, %s, 'paid',%s,%s)",
                                (student_name, course_id, amount_paid,remaining_amount,fee))
                    mysql.commit()
                    cursor.close()
                    return render_template('pay.html')
                #return redirect(url_for('submit'))
        
        return redirect(url_for('submit'))
    else:
        return redirect(url_for('login'))
        
        
@app.route('/student_index', methods=['GET', 'POST'])
def student_index():
    if request.method == 'GET':
        cursor = mysql.cursor(dictionary=True)  # Enable dictionary cursor
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        cursor.close()
        return render_template('status.html', students=students)
    elif request.method == 'POST':
        student_name = request.form['student_name']
        course_id = request.form['course_id']
        amount_paid = request.form['amount_paid']

        student_status = 'Enrolled'  # Replace this with your logic to determine the status

        # Flash a message with the student's status
        flash(f"The status of student {student_name} is {student_status}")

        return redirect(url_for('student_index'))


# @app.route('/delete/<id>')
# def delete_course(id):
#     cursor = mysql.cursor()
#     cursor.execute("DELETE FROM courses WHERE id = %s", [id])
#     mysql.commit()
#     cursor.close()
#     return redirect(url_for('adminhome'))


if __name__ == '__main__':
    app.run(debug=True)
