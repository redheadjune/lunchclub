from collections import namedtuple

CLIQUE_SIZE = 5
SLOTS = {
		'member': ['id', 'name', 'email', 'successes', 'misses', 'join_date', 'active'],
		'membership': ['member_id', 'clique_id', 'completed', 'active'],
		'clique': ['id', 'start_date', 'end_date'],
		'lunch': ['clique_id', 'member_one', 'member_two', 'completed'],
		}

SCHEMA_INFO = {}
for slot, slot_info in SLOTS.iteritems():
	SCHEMA_INFO[slot] = {
			'slots': slot_info,
			'namedtuple': namedtuple('%s_named_tuple' % slot, slot_info),
			}

DEMO = {
		'members': [
			{
				'name': 'Scott Clark',
				'email': 'sclark'
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
			{
				'name': 'Ironman',
				'email': 'stark',
				},
			{
				'name': 'Jean Grey',
				'email': 'phoenix',
				},
			{
				'name': 'Wolverine',
				'email': 'logan',
				},
			{
				'name': 'Thor',
				'email': 'blondie',
				},

			],
		}

