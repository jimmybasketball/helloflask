from flask import Flask,flash,redirect,render_template,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import  FlaskForm
from wtforms import  TextAreaField,SubmitField
from wtforms.validators import DataRequired
from flask_migrate import Migrate

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://mha:mhapwd@172.19.2.52:3306/mj_test'
app.config['SECRET_KEY'] = 'secret_key'
migrate = Migrate(app,db)

#添加shell上下文处理函数
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Note=Note, Author=Author, Article=Article,Writer=Writer,Book=Book,
                Post=Post,Comment=Comment,Draft=Draft)

class Note(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    def __repr__(self):
        return '<Note %r>'% self.body

#创建表单,包含一个输入框和提交
class NewNoteForm(FlaskForm):
    body = TextAreaField('Body',validators=[DataRequired()])
    submit = SubmitField('Save')
#更新表单
class EditNoteForm(FlaskForm):
    body = TextAreaField('Body',validators=[DataRequired()])
    submit = SubmitField('Update')

#删除表单
class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')

#创建一个new_note视图,
#声明一个表单类，校验输入和确定，取输入值给body，再new一个note数据库实例，写入数据
@app.route('/new',methods=['GET','POST'])
def new_note():
    form = NewNoteForm()
    if form.validate_on_submit():
        body = form.body.data
        note = Note(body=body)
        db.session.add(note)
        db.session.commit()
        # db.create_all()
        flash('Your note is saved')
        return redirect(url_for('index'))
    return render_template('new_note.html',form=form)

#更新数据视图，new一个更新表单，查询出ID更新
@app.route('/edit/<int:note_id>',methods=['GET','POST'])
def edit_note(note_id):
    form = EditNoteForm()
    note = Note.query.get(note_id)
    if form.validate_on_submit():
        note.body = form.body.data
        db.session.commit()
        flash('your note is updated')
        return redirect(url_for('index'))
    #在get请求中，把数据库的改条记录展示出来（展示出原来未更新的数据）
    form.body.data = note.body
    return render_template('edit_note.html',form=form)

@app.route('/')
def index():
    form = DeleteForm()
    notes = Note.query.all()
    return render_template('index.html',form=form,notes=notes)
#删除视图
@app.route('/delete/<note_id>',methods=['POST'])
def delete_note(note_id):
    form = DeleteForm()
    note = Note.query.get(note_id)
    if form.validate_on_submit():
        db.session.delete(note)
        db.session.commit()
        flash('your note is deleted')
        return redirect(url_for('index'))
    return render_template('index.html')


# one to many
class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    phone = db.Column(db.String(20))
    articles = db.relationship('Article')  # collection

    def __repr__(self):
        return '<Author %r>' % self.name


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), index=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __repr__(self):
        return '<Article %r>' % self.title

# one to many + bidirectional relationship
class Writer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    books = db.relationship('Book', back_populates='writer')

    def __repr__(self):
        return '<Writer %r>' % self.name


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True)
    writer_id = db.Column(db.Integer, db.ForeignKey('writer.id'))
    writer = db.relationship('Writer', back_populates='books')

    def __repr__(self):
        return '<Book %r>' % self.name
# cascade,级联操作，关键字cascade,父级的元素修改，删除，子级对应的也变化
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    body = db.Column(db.Text)
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')  # collection


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', back_populates='comments')  # scalar

# event listening监听
class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    edit_time = db.Column(db.Integer, default=0)


@db.event.listens_for(Draft.body, 'set')
def increment_edit_time(target, value, oldvalue, initiator):
    if target.edit_time is not None:
        target.edit_time += 1

db.create_all()