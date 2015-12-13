from flask import render_template, redirect, request, jsonify, send_file
from flask.ext.login import current_user, login_required
from .. import db
from ..models import Sample
from ..models import SampleType
from ..models import Action
from ..models import ActionType
from ..models import SMBResource
from ..models import SAMPLE_NAME_LENGTH   # <-- sort this out
from . import main
from forms import NewSampleForm, NewActionForm, NewMatrixForm
from datetime import date, datetime



# see http://flask.pocoo.org/snippets/67/
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@main.route('/')
@login_required
def index():
    samples=Sample.query.filter_by(owner=current_user)
    return render_template('editor.html', samples=samples, sampletypes=SampleType.query.all(),
                           actiontypes=ActionType.query.all())


@main.route('/allsamples')
@login_required
def allsamples():
    if current_user.is_admin:
        return render_template('allsamples.html', samples=Sample.query.all())
    else:
        return render_template('404.html'), 404


@main.route('/sample/<sampleid>', methods=['GET', 'POST'])
@login_required
def sampleeditor(sampleid):
    sample = Sample.query.get(sampleid)
    samples = Sample.query.filter_by(owner=current_user)
    if sample == None or sample.owner != current_user:
        return render_template('404.html'), 404
    else:
        form = NewActionForm()
        form.actiontype.choices = [(actiontype.id, actiontype.name) for actiontype in ActionType.query.order_by('name')]
        form.description.data = ''
        form.timestamp.data = date.today()
        if (request.args.get("editorframe") == "true"):
            return render_template('editorframe.html', samples=samples, sample=sample,
                                   actions=sample.actions, form=form, sampletypes=SampleType.query.all(),
                                   actiontypes=ActionType.query.all())
        else:
            return render_template('editor.html', samples=samples, sample=sample, actions=sample.actions,
                                   form=form, sampletypes=SampleType.query.all(), actiontypes=ActionType.query.all())


@main.route('/changesamplename', methods=['POST'])
@login_required
def changesamplename():
    sample = Sample.query.filter_by(id=int(request.form.get("id"))).first()
    if sample == None or sample.owner != current_user:
        return jsonify(code=1, error="Sample does not exist or you do not have the right to access it")
    newname = request.form.get('value')
    if len(newname) > SAMPLE_NAME_LENGTH:
        return jsonify(code=1, error="Name too long", name=sample.name)
    if (Sample.query.filter_by(name=newname).first() == None):
        sample.name = newname
        db.session.commit()
        return jsonify(code=0, name=newname, id=sample.id)
    else:
        return jsonify(code=1, error="Name is already taken", name=sample.name)


@main.route('/changesampletype', methods=['POST'])
@login_required
def changesampletype():
    sample = Sample.query.filter_by(id=int(request.form.get("id"))).first()
    if sample == None or sample.owner != current_user:
        return jsonify(code=1, error="Sample does not exist or you do not have the right to access it")
    sample.sampletype_id = int(request.form.get('value'))
    db.session.commit()
    return sample.sampletype.name


@main.route('/changesampleimage', methods=['POST'])
@login_required
def changesampleimage():
    sample = Sample.query.filter_by(id=int(request.form.get("id"))).first()
    if sample == None or sample.owner != current_user:
        return jsonify(code=1, error="Sample does not exist or you do not have the right to access it")
    sample.image = request.form.get('value')
    db.session.commit()
    return ""


@main.route('/changeactiondate', methods=['POST'])
@login_required
def changeactiondate():
    action = Action.query.filter_by(id=int(request.form.get("id"))).first()
    if action == None or action.sample.owner != current_user:
        return jsonify(code=1, error="Action does not exist or you do not have the right to access it")
    try:
        action.timestamp = datetime.strptime(request.form.get('value'), '%Y-%m-%d')
    except ValueError:
        return jsonify(code=1, error="Not a valid date", id=action.id, date=action.timestamp.strftime('%Y-%m-%d'))
    db.session.commit()
    return jsonify(code=0, id=action.id, date=action.timestamp.strftime('%Y-%m-%d'))


@main.route('/changeactiontype', methods=['POST'])
@login_required
def changeactiontype():
    action = Action.query.filter_by(id=int(request.form.get("id"))).first()
    if action == None or action.sample.owner != current_user:
        return jsonify(code=1, error="Action does not exist or you do not have the right to access it")
    action.actiontype_id = request.form.get('value')
    db.session.commit()
    return action.actiontype.name


@main.route('/changeactiondesc', methods=['POST'])
@login_required
def changeactiondesc():
    action = Action.query.filter_by(id=int(request.form.get("id"))).first()
    if action == None or action.sample.owner != current_user:
        return jsonify(code=1, error="Action does not exist or you do not have the right to access it")
    action.description = request.form.get('value')
    db.session.commit()
    return action.description


@main.route('/delaction/<actionid>', methods=['GET', 'POST'])
@login_required
def deleteaction(actionid):
    action = Action.query.filter_by(id=int(actionid)).first()
    if action == None or action.sample.owner != current_user:
        return render_template('404.html'), 404
    sampleid = action.sample_id
    db.session.delete(action)
    db.session.commit()
    return redirect("/sample/" + str(sampleid))


@main.route('/delsample/<sampleid>', methods=['GET', 'POST'])
@login_required
def deletesample(sampleid):
    sample = Sample.query.filter_by(id=int(sampleid)).first()
    if sample == None or sample.owner != current_user:
        return render_template('404.html'), 404
    db.session.delete(sample)  # delete cascade automatically deletes associated actions
    db.session.commit()
    return redirect("/")


@main.route('/changeparent', methods=['POST'])
@login_required
def changeparent():
    sample = Sample.query.filter_by(id=int(request.form.get("id"))).first()
    if sample == None or sample.owner != current_user:
        return jsonify(code=1, error="Sample does not exist or you do not have the right to access it")

    # check if we're not trying to make the snake bite its tail
    parentid = int(request.form.get('parent'))
    if (parentid != 0):
        p = Sample.query.filter_by(id=parentid).first()
        while (p.parent_id != 0):
            if (p.parent_id == sample.id):
                return "Can't move item"
            p = p.parent

    sample.parent_id = parentid
    db.session.commit()
    return ""


@main.route('/newsample', methods=['GET', 'POST'])
@login_required
def newsample():
    form = NewSampleForm()
    form.sampletype.choices = [(sampletype.id, sampletype.name) for sampletype in SampleType.query.order_by('name')]
    form.parent.choices = [(0, "/")] + [(sample.id, sample.name) for sample in Sample.query.order_by('name')]
    if form.validate_on_submit():
        sample = Sample(owner=current_user, name=form.name.data, sampletype_id=form.sampletype.data, parent_id=form.parent.data)
        db.session.add(sample)
        db.session.commit()
        return redirect("/sample/" + str(sample.id))
    return render_template('newsample.html', form=form)


@main.route('/newaction/<sampleid>', methods=['POST'])
@login_required
def newaction(sampleid):
    sample = Sample.query.filter_by(id=int(sampleid)).first()
    if sample == None or sample.owner != current_user:
        return jsonify(code=1, error="Sample does not exist or you do not have the right to access it")

    form = NewActionForm()
    form.actiontype.choices = [(actiontype.id, actiontype.name) for actiontype in ActionType.query.order_by('name')]
    if form.validate_on_submit():  # what about CSRF protection?? (see http://flask-wtf.readthedocs.org/en/latest/csrf.html)
        print form.timestamp.data
        print form.actiontype.data
        print form.description.data
        db.session.add(Action(timestamp=form.timestamp.data, sample_id=sampleid, actiontype_id=form.actiontype.data,
                              description=form.description.data))
        db.session.commit()
    return ""



@main.route('/matrixview/<sampleid>', methods=['GET', 'POST'])
def matrixview(sampleid):
    sample = Sample.query.filter_by(id=int(sampleid)).first()
    form = NewMatrixForm()
    if form.validate_on_submit():  # TODO: do this with AJAX
        sample.mheight = int(form.height.data)
        sample.mwidth = int(form.width.data)
        db.session.commit()
    matrix = []
    children = sample.children

    if (sample.mheight):
        for y in range(sample.mheight):
            mrow = []
            for x in range(sample.mwidth):
                element = 0
                for c in range(len(children)):
                    if children[c].mx == x and children[c].my == y:
                        element = children[c].id
                mrow.append(element)
            matrix.append(mrow)

    return render_template('matrixview.html', sample=sample, form=form, matrix=matrix)


@main.route('/childbrowser/<sampleid>')
def childbrowser(sampleid):
    sample = Sample.query.filter_by(id=int(sampleid)).first()
    return render_template('childbrowser.html', sample=sample)


@main.route('/setmatrixcoords/<sampleid>', methods=['POST'])
def setmatrixcoords(sampleid):
    sample = Sample.query.filter_by(id=int(sampleid)).first()
    sample.mx = int(request.form.get('mx'))
    sample.my = int(request.form.get('my'))
    db.session.commit()
    return ""