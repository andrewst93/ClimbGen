import sqlite3, json, sys, atexit
import stats

# Implements a parser for the SQLite database for the Tension Board app
# Provides helper and various utiltiy functions
class DBReader:
    def __init__(self):
        self.db = sqlite3.connect(r'..\Data\db\f\db-105.sqlite3')
        self.db.row_factory = sqlite3.Row
        atexit.register(self.close)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.db.close()

    def get_grade_row(self, grade: str) -> list:
        command = '''
            SELECT difficulty, french_name, yds_name, verm_name
            FROM difficulty_grades 
            WHERE verm_name=? COLLATE NOCASE or 
            french_name=? COLLATE NOCASE or 
            yds_name=? COLLATE NOCASE or
            difficulty=? COLLATE NOCASE
        '''
        return self.db.execute(command, (grade,)*4).fetchall()

    def get_grade(self, grade: str) -> list:
        return [x[0] for x in self.get_grade_row(grade)]

    def get_v_grade(self, grade: str) -> list:
        return self.get_grade_row(grade)[0]['verm_name']

    def get_climbs_of_grade(self, grade: list, min_rating=0.0):
        command = '''
            SELECT * 
            FROM climbs
            INNER JOIN climb_stats on climb_stats.climb_uuid=climbs.uuid
            WHERE climb_stats.difficulty_average BETWEEN ? AND ? 
            AND climb_stats.quality_average >= ?
            ORDER BY climb_stats.quality_average
        '''
        return self.db.execute(command, (grade[0], grade[-1], min_rating)).fetchall()

    def get_climb_by_name(self, name: str):
        return self.db.execute('SELECT * FROM climbs WHERE name=?', (name,)).fetchone()

    def get_climb_row_info(self, climb):
        return '{}, Grade: {}, Ascents: {}, Setter: {}, FA: {}, Rating: {:.1f}'.format(
            climb['name'],
            self.get_v_grade(int(climb['difficulty_average'])),
            climb['ascensionist_count'],
            climb['setter_username'],
            self.db.execute('SELECT fa_username from climb_stats WHERE climb_uuid=?', (climb['uuid'],)).fetchone()[0],
            climb['quality_average'])

    def export_climbs(self, name: str, climbs: list):
        climb_data = []
        for climb in climbs:
            data = self.db.execute('SELECT placement_id, role_id from climbs_placements where climb_uuid=?', (climb['uuid'],)).fetchall()
            climb_data.append({
                'Name': climb['name'],
                'Holds': [x[0] for x in data],
                'Roles': [x[0] for x in data]
            })
        self.export_json(name, climb_data)

    def export_holds_data(self):
        holes_data = self.db.execute('SELECT * from placements INNER JOIN holes on hole_id=holes.id').fetchall()
        data = []
        for row in holes_data:
            data.append({
                'Id': row['hold_id'],
                'Name': row['name'],
                'Coord X': row['x'],
                'Coord Y': row['y'],
                'Mirror Id': row['mirrored_hole_id']
            })
        self.export_json('holds_data.json', data)

    def export_json(self, name: str, data: list):
        path = name + '.json' if not name.endswith('.json') else name
        with open(path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f'{path} saved successfully')

    def output_stats(self):
        stats.output_stats(self)


# Split args from a single raw string into a list of args
# # (quoted args are kept together / as one arg, otherwise we split on space)
def split_args(args_raw):
    args = []
    arg = ''
    quote = False

    for c in args_raw:
        if c == '"':
            if quote:
                args.append(arg)
                arg = ''
            quote = not quote
        elif not quote and c == ' ':
            if len(arg) > 0:
                args.append(arg)
                arg = ''
        else:
            arg += c

    if len(arg) > 0:
        args.append(arg)
    return args

# Try to perform a command from an input
def try_command(commands, command):
    args_start = command.find(' ')
    args_raw = '' if args_start == -1 else command[args_start+1:]
    command = command if args_start == -1 else command[:args_start]

    if command.lower() in commands:
        try:
            commands[command](*split_args(args_raw))
        except TypeError:
            print('Invalid arguments')
        except Exception as e:
            print(e)
    else:
        print('Invalid command')

# Create the reader object (and auto dispose of it, which closes the SQLite DB connection)
with DBReader() as reader:

    # All possible commands - dictionary mapped to a lambda that performs the action
    COMMANDS = {
        'help': lambda: print('Commands: {}'.format(', '.join(COMMANDS.keys()))),
        'v_grade': lambda grade: print(reader.get_v_grade(grade)),
        'output_stats': reader.output_stats,
        'export_climb': lambda climb: reader.export_climbs(climb, [reader.get_climb_by_name(climb)]),
        'export_climbs': lambda grade: reader.export_climbs('climbs_' + grade, reader.get_climbs_of_grade(reader.get_grade(grade))),
        'export_all_climbs': lambda: reader.export_climbs('climbs_all', reader.get_climbs_of_grade([0, 999])),
        'export_all_climbs_split': lambda: [reader.export_climbs(f'climbs_v{x}', reader.get_climbs_of_grade(reader.get_grade(f'v{x}'))) for x in range(0, 17)],
        'export_holds_data': reader.export_holds_data,
        'quit': quit
    }
    
    if __name__ == '__main__':
        while True:
            try_command(COMMANDS, input())
    else:
        try_command(COMMANDS, ' '.join(sys.argv))