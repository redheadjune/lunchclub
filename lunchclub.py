import sqlite3
import datetime
import math
import random
import json
import pprint
pp = pprint.PrettyPrinter(indent=4)
from collections import namedtuple
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing

CLIQUE_SIZE = 5
MEMBER_SLOTS = ['id', 'name', 'email', 'successes', 'misses', 'join_date', 'active']
MEMBERSHIP_SLOTS = ['member_id', 'clique_id', 'completed', 'active']
CLIQUE_SLOTS = ['id', 'start_date', 'end_date']
LUNCH_SLOTS = ['clique_id', 'member_one', 'member_two', 'completed']
SCHEMA_INFO = {
		'member': {
			'slots': MEMBER_SLOTS,
			'namedtuple': namedtuple('Member', MEMBER_SLOTS)
			},
		'membership': {
			'slots': MEMBERSHIP_SLOTS,
			'namedtuple': namedtuple('Membership', MEMBERSHIP_SLOTS)
			},
		'clique': {
			'slots': CLIQUE_SLOTS,
			'namedtuple': namedtuple('Clique', CLIQUE_SLOTS)
			},
		'lunch': {
			'slots': LUNCH_SLOTS,
			'namedtuple': namedtuple('Lunch', LUNCH_SLOTS)
			},
		}

# configuration
DATABASE = '/tmp/lunchclub.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = connect_db()
	return db

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

def query_db_for_type(query, schema, args=(), one=False):
	result_tuples = query_db(query, args, one)
	if not one:
		results = []
		for _, result_tuple in enumerate(result_tuples):
			result_list = list(result_tuple)
			for i, slot_name in enumerate(schema['slots']):
				if 'date' in slot_name:
					result_list[i] = datetime.datetime.fromordinal(result_tuple[i]).date()
			results.append(schema['namedtuple']._make(result_list))
	else:
		if result_tuples:
			result_list = list(result_tuples)
			for i, slot_name in enumerate(schema['slots']):
				if 'date' in slot_name:
					result_list[i] = datetime.datetime.fromordinal(result_tuples[i]).date()
			results = schema['namedtuple']._make(result_list)
		else:
			return None
	return results

def commit_lunch(clique_id, member_one_id, member_two_id, completed=1):
	db = get_db()
	db.execute('update lunch set completed=%d where clique_id=%d and member_one=%d and member_two=%d' %
			(completed, int(clique_id), int(member_one_id), int(member_two_id))
			)
	db.execute('update lunch set completed=%d where clique_id=%d and member_one=%d and member_two=%d' %
			(completed, int(clique_id), int(member_two_id), int(member_one_id))
			)
	db.commit()

@app.route('/lunch/remove', methods=['POST'])
def remove_lunch():
	commit_lunch(
			int(request.form['clique_id']),
			int(request.form['member_one']),
			int(request.form['member_two']),
			completed=0
			)

	return redirect('/members/%s' % request.form['member_email'])

@app.route('/lunch/add', methods=['POST'])
def add_lunch():
	print request.form
	commit_lunch(
			int(request.form['clique_id']),
			int(request.form['member_one']),
			int(request.form['member_two'])
			)

	return redirect('/members/%s' % request.form['member_email'])

@app.route('/')
@app.route('/members')
def show_members():
	members = query_db_for_type(
			'select id, name, email, successes, misses, join_date, active from member order by join_date desc',
			SCHEMA_INFO['member'],
			)
	return render_template('show_members.html', members=members)

@app.route('/members/<member_email>')
def show_member(member_email):
	member_info = query_db_for_type(
			'select id, name, email, successes, misses, join_date, active from member where email="%s"' %
			str(member_email),
			SCHEMA_INFO['member'],
			one=True
			)
	if not member_info:
		flash('No such user')
		return redirect(url_for('show_members'))
	
	memberships = query_db_for_type(
			'select member_id, clique_id, completed, active from membership where member_id=%d' %
			member_info.id,
			SCHEMA_INFO['membership']
			)

	clique_ids = []
	for membership in memberships:
		if membership.active:
			clique_ids.append(membership.clique_id)
	
	cliques = query_db_for_type(
			'select id, start_date, end_date from clique where id in (%s)' %
			','.join('?'*len(clique_ids)),
			SCHEMA_INFO['clique'],
			args=clique_ids,
			)

	lunches = query_db_for_type(
			'select clique_id, member_one, member_two, completed from lunch where clique_id in (%s)' %
			','.join('?'*len(clique_ids)),
			SCHEMA_INFO['lunch'],
			args=clique_ids,
			)

	for lunch in lunches:
		print lunch

	lunch_dict = {}
	member_id_list = []
	for lunch in lunches:
		if lunch.member_one is not member_info.id and lunch.member_one not in member_id_list:
			member_id_list.append(lunch.member_one)
		if lunch.member_two is not member_info.id and lunch.member_two not in member_id_list:
			member_id_list.append(lunch.member_two)
		if lunch.clique_id not in lunch_dict:
			lunch_dict[lunch.clique_id] = []
		lunch_dict[lunch.clique_id].append(lunch)

	lunch_members = query_db_for_type(
			'select id, name, email, successes, misses, join_date, active from member where id in (%s)' %
			','.join('?'*len(member_id_list)),
			SCHEMA_INFO['member'],
			args=member_id_list,
			)

	lunch_members_by_id = {}
	for lunch_member in lunch_members:
		lunch_members_by_id[lunch_member.id] = lunch_member

	member_dict = {
			'member': member_info,
			'cliques': {}
			}

	for clique in cliques:
		member_dict['cliques'][clique.id] = {
				'completed': 0,
				'total': 0,
				'lunches': {}
				}
		for lunch in lunch_dict[clique.id]:
			if lunch.member_two == member_info.id:
				member_dict['cliques'][clique.id]['completed'] += lunch.completed
				member_dict['cliques'][clique.id]['total'] += 1
				member_dict['cliques'][clique.id]['lunches'][lunch_members_by_id[lunch.member_one].name] = {
						'completed': lunch.completed,
						'alias': lunch_members_by_id[lunch.member_one].email,
						'id': lunch_members_by_id[lunch.member_one].id
						}
			elif lunch.member_one == member_info.id:
				member_dict['cliques'][clique.id]['completed'] += lunch.completed
				member_dict['cliques'][clique.id]['total'] += 1
				member_dict['cliques'][clique.id]['lunches'][lunch_members_by_id[lunch.member_two].name] = {
						'completed': lunch.completed,
						'alias': lunch_members_by_id[lunch.member_two].email,
						'id': lunch_members_by_id[lunch.member_two].id
						}

	print member_dict


	return render_template('show_member.html', member_dict=member_dict)

@app.route('/members/add', methods=['POST'])
def add_member():
	db = get_db()
	db.execute('insert into member (name, email, successes, misses, join_date, active) values (?, ?, ?, ?, ?, ?)',
			[request.form['name'], request.form['alias'], 0, 0, datetime.date.today().toordinal(), True])
	db.commit()
	flash('New user added')
	return redirect(url_for('show_members'))

DEMO = {
		'members': [
			{
				'name': 'Scott Clark',
				'email': 'sclark'
				},
			{
				'name': 'Eric Liu',
				'email': 'eliu',
				},
			{
				'name': 'Marin Saric',
				'email': 'msaric',
				},
			{
				'name': 'Frane Saric',
				'email': 'fsaric',
				},
			{
				'name': 'Grace Lee',
				'email': 'glee',
				},
			{
				'name': 'Batman',
				'email': 'thebatman',
				},
			{
				'name': 'Spiderman',
				'email': 'spidey',
				},
			{
				'name': 'The Hulk',
				'email': 'greenman',
				},
			{
				'name': 'Superman',
				'email': 'manofsteel',
				},
			],
		}
@app.route('/demo_load')
def demo_load():
	db = get_db()
	db.execute('delete from member')
	db.execute('delete from clique')
	db.execute('delete from membership')
	db.execute('delete from lunch')
	for member in DEMO['members']:
		db.execute('insert into member (name, email, successes, misses, join_date, active) values (?, ?, ?, ?, ?, ?)',
				[member['name'], member['email'], 0, 0, datetime.date.today().toordinal(), True])
	db.commit()
	clique_maker()
	flash('New user added')
	return redirect(url_for('show_members'))

def get_all_cliques(force_active=True, require_member=None):
	memberships = query_db_for_type(
			'select member_id, clique_id, completed, active from membership',
			SCHEMA_INFO['membership']
			)
	active_cliques = {}
	active_member_ids = []
	for membership in memberships:
		if membership.active or not force_active:
			if membership.clique_id not in active_cliques:
				active_cliques[membership.clique_id] = {
						'members': {
							membership.member_id: {}
							}
						}
			else:
				active_cliques[membership.clique_id]['members'][membership.member_id] = {}
			active_member_ids.append(membership.member_id)

	if require_member is not None:
		delete_list = []
		for clique_id, clique in active_cliques.iteritems():
			if require_member not in clique['members']:
				delete_list.append(clique_id)
		for delete_id in delete_list:
			active_cliques.pop(delete_id)

	if len(active_cliques) > 0:
		cliques = query_db_for_type(
				'select id, start_date, end_date from clique where id in (%s)' %
				','.join('?'*len(active_cliques.keys())),
				SCHEMA_INFO['clique'],
				args=active_cliques.keys(),
				)
	else:
		return {}

	for clique in cliques:
		active_cliques[clique.id]['start_date'] = clique.start_date
		active_cliques[clique.id]['end_date'] = clique.end_date

	if len(active_member_ids) > 0:
		members = query_db_for_type(
				'select id, name, email, successes, misses, join_date, active from member where id in (%s)' %
				','.join('?'*len(active_member_ids)),
				SCHEMA_INFO['member'],
				args=active_member_ids,
				)
	else:
		return {}

	lunches = query_db_for_type(
			'select clique_id, member_one, member_two, completed from lunch where clique_id in (%s)' %
			','.join('?'*len(active_cliques.keys())),
			SCHEMA_INFO['lunch'],
			args=active_cliques.keys(),
			)

	lunch_dict = {}
	for lunch in lunches:
		if lunch.clique_id not in lunch_dict:
			lunch_dict[lunch.clique_id] = {}
		lunch_dict[lunch.clique_id][(lunch.member_one, lunch.member_two)] = lunch.completed

	active_members = {}
	for member in members:
		active_members[member.id] = {
				'name': member.name,
				'email': member.email,
				}

	for clique_id, clique in active_cliques.iteritems():
		for member_id, member_info in clique['members'].iteritems():
			member_info['name'] = active_members[member_id]['name']
			member_info['email'] = active_members[member_id]['email']
		clique['connections'] = lunch_dict[clique_id]

	return active_cliques

def clique_maker():
	members = query_db_for_type(
			'select id, name, email, successes, misses, join_date, active from member order by join_date desc',
			SCHEMA_INFO['member'],
			)
	number_of_cliques = int(math.ceil(len(members)/float(CLIQUE_SIZE)))
	start_date = datetime.date.today().toordinal()
	end_date = start_date + 30 # One month later

	clique_membership = []
	for _ in range(number_of_cliques):
		clique_membership.append([])

	members = list(members)
	num_members = len(members)
	for member_on in range(num_members):
		clique_on = member_on % number_of_cliques
		clique_membership[clique_on].append(
				members.pop(random.randint(0, len(members) - 1))
				)

	db = get_db()
	db.execute('update membership set active=0')
	for clique in clique_membership:
		cursor = db.execute('insert into clique (start_date, end_date) values (?, ?)',
				[start_date, end_date])
		clique_id = cursor.lastrowid
		for member in clique:
			db.execute('insert into membership (member_id, clique_id, completed, active) values (?, ?, ?, ?)',
					[member.id, clique_id, False, True])
			for other_member in clique:
				if member.id < other_member.id:
					db.execute('insert into lunch (clique_id, member_one, member_two, completed) values (?, ?, ?, ?)',
							[clique_id, member.id, other_member.id, False])
	db.commit()

@app.route('/cliques/make')
def make_cliques():
	clique_maker()
	return redirect(url_for('show_cliques'))

@app.route('/cliques/destroy')
def destroy_cliques():
	db = get_db()
	db.execute('delete from clique')
	db.execute('delete from membership')
	db.commit()
	return redirect(url_for('show_cliques'))

@app.route('/cliques')
def show_cliques():
	active_cliques = get_all_cliques()
	return render_template('show_cliques.html', cliques=active_cliques)

def cliques_to_json_for_d3(active_cliques):
	json_data = {
			'nodes': [],
			'links': [],
			'labelAnchors': [],
			'labelAnchorLinks': [],
			}
	member_to_node = {}
	node_on = 0
	for clique_id, clique in active_cliques.iteritems():
		for member_id, member in clique['members'].iteritems():
			node = {
					"label": '%s (%s)' % (member['name'], member['email']),
					}
			json_data['nodes'].append(node)
			json_data['labelAnchors'].append({"node": node_on})
			json_data['labelAnchors'].append({"node": node_on})
			json_data['labelAnchorLinks'].append(
					{
						"source": node_on * 2,
						"target": node_on * 2 + 1,
						"weight": 1,
						}
					)

			member_to_node[member_id] = node_on
			node_on += 1
		for connection, completed in clique['connections'].iteritems():
			json_data['links'].append(
					{
						"source": member_to_node[connection[0]],
						"target": member_to_node[connection[1]],
						"weight": completed
					}
					)
	return json_data

@app.route('/members/<member_email>/clique_data')
def clique_member_data(member_email):
	member_info = query_db_for_type(
			'select id, name, email, successes, misses, join_date, active from member where email="%s"' %
			str(member_email),
			SCHEMA_INFO['member'],
			one=True
			)
	if not member_info:
		return '{}'
	active_cliques = get_all_cliques(require_member=member_info.id)
	json_data = cliques_to_json_for_d3(active_cliques)
	return json.dumps(json_data)

@app.route('/cliques/clique_data')
def clique_data():
	active_cliques = get_all_cliques()
	json_data = cliques_to_json_for_d3(active_cliques)
	return json.dumps(json_data)

if __name__ == '__main__':
	app.run()
