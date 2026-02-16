from flask import Blueprint, render_template, request,redirect,url_for,flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from ..models import User, Character, Tasks, SubTasks, XPSTAT, ChatMessages, ChatSession

from ..extensions import db
from ..chat import checkQuota,FREETOKENSMAX, PREMIUMTOKENSMAX,darjahai
from sqlalchemy.exc  import IntegrityError

from ..analysis import builder, save_top_terms, termstorun, run_analysis_latest, runhistory

from datetime import datetime,timezone,date
from ..levelup import addXP, XPFORTASK
import os,stripe



bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/home")
def home():
    return render_template("home.html")

@bp.route("/about")
def about():
    return render_template("about.html")

@bp.route("/dashboard",methods=["GET","POST"])
@login_required
def dashboard():
    tasks = (
    Tasks.query.filter_by(user_id=current_user.id)
    .order_by(Tasks.task_date_created.desc()).all())

    selected_task_id= request.args.get("task_id",type=int)

    if selected_task_id:
        subtasks = (
            SubTasks.query.filter_by(user_id=current_user.id, task_id=selected_task_id)
            .order_by(SubTasks.subtask_date_created.desc())
            .all())
    else:
        subtasks=[]

    return render_template("dashboard.html",tasks=tasks, subtasks=subtasks,selected_task_id=selected_task_id)




@bp.route("/verify-error")
def verify_error():
    return render_template("verify_error.html")

@bp.route("/reset-password-error")
def reset_password_error():
    return render_template("reset_password_error.html")

@bp.route("/tasks",methods=["GET","POST"])
@login_required
def tasks():

    if request.method=="POST":
        task_name = (request.form.get("TaskName") or "").strip()
        task_id = (request.form.get("TaskID") or "").strip()
        task_category = (request.form.get("TaskCategory") or "").strip()
        task_status = (request.form.get("TaskStatus") or "").strip()
        task_priority = (request.form.get("TaskPriority") or "").strip()
        task_description = (request.form.get("TaskDescription") or "").strip()
        task_location = (request.form.get("TaskLocation") or "").strip()
        task_due_date_entered = (request.form.get("TaskDueDateEntered") or "").strip()

        
        if not task_name or not task_id or not task_category or not task_status or not task_priority or not task_description or not task_location or not task_due_date_entered:
            flash("One or more of your fields is not filled in.","danger")
            return redirect(url_for("main.tasks"))
        
        

        new_task= Tasks(task_name=task_name,
                        task_id=task_id,
                        task_category=task_category,
                        task_status=task_status,
                        task_priority=task_priority,
                        task_description=task_description,
                        task_location=task_location,
                        task_due_date_entered=task_due_date_entered
                        ,user_id=current_user.id)
        db.session.add(new_task)

        try:
            db.session.flush()
            res = builder(db.session,current_user.id)
            run_id = res.get("run_id")
            top_terms = res.get("top_terms",[])
            save_top_terms(current_user.id,run_id,top_terms)
            db.session.commit()
            flash("Task successfully created", "success")
        except IntegrityError:
            db.session.rollback()
            flash("Task ID or Name already exist.","danger")
        except Exception:
            db.session.rollback()
            flash("Error. Can not create the task.","danger")

        return redirect(url_for("main.dashboard"))

    return render_template("tasks.html")

@bp.route("/tasks/update",methods=["POST"])
@login_required
def update_tasks():
    ids = request.form.getlist("task_db_id[]")
    task_ids = request.form.getlist("task_id[]")
    task_names = request.form.getlist("task_name[]")
    task_categories = request.form.getlist("task_category[]")
    task_statuses = request.form.getlist("task_status[]")
    task_priorities = request.form.getlist("task_priority[]")
    task_descriptions = request.form.getlist("task_description[]")
    task_locations = request.form.getlist("task_location[]")
    task_due_dates = request.form.getlist("task_due_date_entered[]")
    task_reminders= request.form.getlist("task_reminder_status[]")

    try:
        totalLevelGained=0
        finalLevel= None
        for i in range(len(ids)):
            task =Tasks.query.filter_by(id=int(ids[i]),
            user_id=current_user.id).first()
            
            if not task:
                continue

            old_status = task.task_status


            task.task_id = (task_ids[i] or "").strip()
            task.task_name = (task_names[i] or "").strip()
            task.task_category = (task_categories[i] or "").strip()
            task.task_status = (task_statuses[i] or "").strip()
            task.task_priority = (task_priorities[i] or "").strip()
            task.task_description = (task_descriptions[i] or "").strip()
            task.task_location = (task_locations[i] or "").strip()
            task.task_due_date_entered = (task_due_dates[i] or "").strip()
            task.task_reminder_status = (task_reminders[i] or "").strip()

            new_status=(task_statuses[i] or "").strip()

            if new_status=="Complete":
                task.task_reminder_status="OFF"

            if old_status != 'Complete' and new_status== 'Complete':
                character= Character.query.filter_by(user_id=current_user.id).first()
                if character:
                    g= addXP(character,XPFORTASK,f"Completed TASK!!! {task.task_name}",XPSTAT)
                    if g>0:
                        totalLevelGained+=g
                        finalLevel= character.level
                    
                    
                    if character.level>=5 and character.level<10:
                        character.c_class="Apprentice"
                    elif character.level>=10 and character.level<20:
                        character.c_class="Mage"
                    elif character.level>=20 and character.level<40:
                        character.c_class="Wizzard Guardian"
                    elif character.level>=40:
                        character.c_class="Magical Task Master"

        
        if totalLevelGained>0:
            flash(f"YOU LEVELED Up!!! GAINED + {totalLevelGained}. You are now level: {finalLevel}","success")

        db.session.flush()
        res = builder(db.session,current_user.id)
        run_id = res.get("run_id")
        top_terms = res.get("top_terms",[])
        save_top_terms(current_user.id,run_id,top_terms)
        db.session.commit()
        flash("Tasks have been updated!","success")
    except IntegrityError:
        db.session.rollback()
        flash("Error. Duplicate Task Name or Task ID")

    except Exception:
        db.session.rollback()
        flash("Error. Can not update.")

    return redirect(url_for("main.dashboard"))


@bp.route("/tasks/delete/<int:task_id>",methods=["POST"])
@login_required
def delete_tasks(task_id: int):
    
    task= Tasks.query.filter_by(id=task_id,user_id=current_user.id).first_or_404()


    try:
        db.session.delete(task)

        db.session.flush()
        res = builder(db.session,current_user.id)
        run_id = res.get("run_id")
        top_terms = res.get("top_terms",[])
        save_top_terms(current_user.id,run_id,top_terms)
        db.session.commit()
        flash("Task deleted.")
    except Exception:
        db.session.rollback()
    
    return redirect(url_for("main.dashboard"))


@bp.route("/tasks/subtasks/<int:task_id>", methods=["POST"])
@login_required
def subtasks(task_id: int):

    if request.method == "POST":
        subtask_name = (request.form.get("SubTaskName") or "").strip()
        subtask_id = (request.form.get("SubTaskID") or "").strip()
        subtask_category = (request.form.get("SubTaskCategory") or "").strip()
        subtask_status = (request.form.get("SubTaskStatus") or "").strip()
        subtask_priority = (request.form.get("SubTaskPriority") or "").strip()
        subtask_description = (request.form.get("SubTaskDescription") or "").strip()
        subtask_location = (request.form.get("SubTaskLocation") or "").strip()
        subtask_due_date_entered = (request.form.get("SubTaskDueDateEntered") or "").strip()

        if (not subtask_name or not subtask_id or not subtask_category or not subtask_status
            or not subtask_priority or not subtask_description or not subtask_location
            or not subtask_due_date_entered):
            flash("One or more of your fields is not filled in.", "danger")
            return redirect(url_for("main.dashboard"))

        parent_task = Tasks.query.filter_by(id=task_id, user_id=current_user.id).first()
        if parent_task is None:
            flash("Task not found.", "danger")
            return redirect(url_for("main.dashboard"))

        new_subtask = SubTasks(
            subtask_name=subtask_name,
            subtask_id=subtask_id,
            subtask_category=subtask_category,
            subtask_status=subtask_status,
            subtask_priority=subtask_priority,
            subtask_description=subtask_description,
            subtask_location=subtask_location,
            subtask_due_date_entered=subtask_due_date_entered,
            user_id=current_user.id,
            task_id=parent_task.id
        )

        db.session.add(new_subtask)

        try:
            db.session.commit()
            flash("SubTask successfully created", "success")
        except IntegrityError:
            db.session.rollback()
            flash("SubTask ID or Name already exist.", "danger")
        except Exception:
            db.session.rollback()
            flash("Error. Can not create the subtask.", "danger")

        return redirect(url_for("main.dashboard"))

    return redirect(url_for("main.dashboard"))


@bp.route("/subtasks/update", methods=["POST"])
@login_required
def update_subtasks():
    selected_task_id= request.args.get("task_id",type=int)

    ids = request.form.getlist("subtask_db_id[]")
    subtask_ids = request.form.getlist("subtask_id[]")
    subtask_names = request.form.getlist("subtask_name[]")
    subtask_categories = request.form.getlist("subtask_category[]")
    subtask_statuses = request.form.getlist("subtask_status[]")
    subtask_priorities = request.form.getlist("subtask_priority[]")
    subtask_descriptions = request.form.getlist("subtask_description[]")
    subtask_locations = request.form.getlist("subtask_location[]")
    subtask_due_dates = request.form.getlist("subtask_due_date_entered[]")
    subtask_reminders = request.form.getlist("subtask_reminder_status[]")

    try:
        for i in range(len(ids)):
            subtask = SubTasks.query.filter_by(
                id=int(ids[i]),
                user_id=current_user.id
            ).first()

            if not subtask:
                continue

            subtask.subtask_id = (subtask_ids[i] or "").strip()
            subtask.subtask_name = (subtask_names[i] or "").strip()
            subtask.subtask_category = (subtask_categories[i] or "").strip()
            subtask.subtask_status = (subtask_statuses[i] or "").strip()
            subtask.subtask_priority = (subtask_priorities[i] or "").strip()
            subtask.subtask_description = (subtask_descriptions[i] or "").strip()
            subtask.subtask_location = (subtask_locations[i] or "").strip()
            subtask.subtask_due_date_entered = (subtask_due_dates[i] or "").strip()
            subtask.subtask_reminder_status = (subtask_reminders[i] or "").strip()

            if subtask.subtask_status == "Complete":
                subtask.subtask_reminder_status = "OFF"

        db.session.commit()
        flash("SubTasks have been updated!", "success")

    except IntegrityError:
        db.session.rollback()
        flash("Error. Duplicate SubTask Name or SubTask ID")

    except Exception:
        db.session.rollback()
        flash("Error. Can not update.")
        
    if selected_task_id:
        return  redirect(url_for("main.dashboard",task_id=selected_task_id))
    

    return redirect(url_for("main.dashboard"))


@bp.route("/subtasks/delete/<int:subtask_id>", methods=["POST"])
@login_required
def delete_subtasks(subtask_id: int):
    subtask = SubTasks.query.filter_by(
        id=subtask_id,
        user_id=current_user.id
    ).first_or_404()

    parent_task_id=subtask.task_id

    db.session.delete(subtask)
    db.session.commit()
    flash("SubTask deleted.")
    return redirect(url_for("main.dashboard",task_id=parent_task_id))

@bp.route("/stats",methods=["GET","POST"])
@login_required
def stats():
    run_id = run_analysis_latest(current_user.id)

    latestterms= []
    history=[]


    select_run_id= request.args.get("run_id")

    if select_run_id:
        run_id=select_run_id
        

    if run_id:
        latestterms=termstorun(current_user.id,run_id,limit=20)
        history=runhistory(current_user.id,limit=15)

    character = Character.query.filter_by(user_id=current_user.id).first()

    
    return render_template("stats.html",run_id=run_id,latestterms=latestterms,history=history,character=character)




@bp.route("/chat/api",methods=["POST"])
@login_required
def chat_api():
    data = request.get_json(silent=True) or {}
    msg= (data.get("message")or "").strip()
    rsession_id=data.get("session_id")
    ok,reason= checkQuota(current_user)


    if not msg:
        return jsonify({"error":"Message required"}), 400
    
    if not ok:
        return jsonify({"error":reason}),429
    db.session.commit()
    try:
        session_id = int(rsession_id) if rsession_id is not None else None
    except (TypeError,ValueError):
        session_id=None

    session= None

    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()

    if session is None:
        session = ChatSession(user_id=current_user.id, title="New Chat", summary=None)
        db.session.add(session)
        db.session.flush()          
        session_id = session.id
   
    try:
        maxoutput = PREMIUMTOKENSMAX if current_user.plan=="premium" else FREETOKENSMAX
        reply= darjahai(current_user.id,msg,session_id=session_id,max_output_tokens=maxoutput)

        db.session.add(ChatMessages(session_id=session_id, role="user", content=msg))
        db.session.add(ChatMessages(session_id=session_id, role="DarjahAI", content=reply))
        session.updated_date = datetime.now(timezone.utc)

        if (session.title or "").lower() == "new chat":
            session.title = msg[:60]

        db.session.commit()

        return jsonify({"reply":reply,"session_id":session_id})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Chat Failed"}),500

@bp.route("/chat",methods=["GET","POST"])
@login_required
def chat():
    sesid= request.args.get("session_id",type=int)

    sessions = (ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_date.desc()).all())

    activeChat= None

    if sesid:
        activeChat= (ChatSession.query.filter_by(id=sesid,user_id=current_user.id).first())

    if activeChat is None and sessions:
        activeChat = sessions[0]

    messages=[]

    if activeChat:
        messages= (ChatMessages.query.filter_by(session_id=activeChat.id).order_by(ChatMessages.created_date.asc()).all())




    return render_template("chat.html",sessions=sessions,activeSessions=activeChat,msgs=messages)

@bp.route("/chat/new",methods=["GET"])
@login_required
def chat_new():
    ses = ChatSession(user_id=current_user.id, title="New Chat", summary=None)
    db.session.add(ses)
    db.session.commit()  

    return redirect(url_for("main.chat", session_id=ses.id))


@bp.route("/chat/delete/<int:session_id>",methods=["POST"])
@login_required
def chat_delete(session_id:int):
    sessionChat= ChatSession.query.filter_by(id=session_id,user_id=current_user.id).first_or_404()
    db.session.delete(sessionChat)
    db.session.commit()
    return redirect(url_for("main.chat"))


stripe.api_key= os.environ["STRIPESECRETKEY"]
prid= os.environ["premiumpriceid"]
ws= os.environ["stripewebhooksecret"]

@bp.route("/billing/checkout",methods=["POST"])
@login_required
def billing_checkout():
    
    ss= stripe.checkout.Session.create(
        line_items=[{"price":prid,"quantity":1}],
        mode="subscription",
        customer_email=current_user.email,
        client_reference_id=str(current_user.id),
        success_url=url_for("main.billing_success",_external=True)+"?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("main.billing_cancel",_external=True),

    )


    return redirect(ss.url,code=303)


@bp.route("/billing/success",methods=["GET"])
@login_required
def billing_success():
    flash("PAYMENT RECEIVED. PREMIUM WILL NOW ACTIVATE","success")
    return redirect(url_for("main.chat"))


@bp.route("/billing/cancel",methods=["GET"])
@login_required
def billing_cancel():
    flash("CHECKOUT CANCELED.","warning")
    return redirect(url_for("main.chat"))

@bp.route("/stripe/webhook",methods=["POST"])
def stripe_webhook():

    pl= request.data
    sig = request.headers.get("Stripe-Signature","")


    try:
        ev= stripe.Webhook.construct_event(pl,sig,ws)
    except ValueError:
        return "Payload Invalid", 400
    except stripe.error.SignatureVerificationError:
        return "Signature Invalid", 400
    
    evt= ev["type"]
    tmp = ev["data"]["object"]

    if evt== "checkout.session.completed":
        user_id = tmp.get("client_reference_id")
        customer_id= tmp.get("customer")
        subscription_id= tmp.get("subscription")

        if user_id:
            user= User.query.filter_by(id=int(user_id)).first()
            if user:
                user.stripeCustomerID= customer_id
                user.stripeSuscriptionID= subscription_id
                db.session.commit()
    elif evt in ("customer.subscription.updated","customer.subscription.deleted"):
        subscription_id= tmp.get("id")
        status= tmp.get("status")

        user= User.query.filter_by(stripeSuscriptionID=subscription_id).first()

        if user:
            user.stripeStatus= status
            user.plan = "premium" if status in ("active","trialing") else "free"
            db.session.commit()

    return "",200
