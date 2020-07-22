import sqlite3, json, sys, atexit

ENABLE_DEBUG_LOGGING = True

class DBReader:
    def __init__(self):
        self.db = sqlite3.connect(r'..\Data\db\f\db-105.sqlite3')
        atexit.register(self.close)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.db.close()

    def get_grade_from_string(self, grade : str) -> list:
        command = '''
            SELECT difficulty, french_name, yds_name, verm_name
            FROM difficulty_grades 
            WHERE verm_name=? COLLATE NOCASE or 
            french_name=? COLLATE NOCASE or 
            yds_name=? COLLATE NOCASE or
            difficulty=? COLLATE NOCASE
        '''
        grade_results = self.db.execute(command, (grade,)*4).fetchall()
        if ENABLE_DEBUG_LOGGING:
            [print('Grade Found: {}'.format(x)) for x in grade_results]
        return [x[0] for x in grade_results]

    def export_climbs(self, name : str, grade : list, rating=None):
        command = '''
            SELECT name 
            FROM climbs
            INNER JOIN climb_stats on climb_stats.climb_uuid = climbs.uuid
            WHERE climb_stats.difficulty_average BETWEEN ? AND ?
        '''
        climbs = self.db.execute(command, (grade[0], grade[-1])).fetchall()

        if ENABLE_DEBUG_LOGGING:
            print('{} climbs found at grade {}'.format(len(climbs), '{} to {}'.format(grade[0], grade[-1]) if len(grade) > 1 else str(grade[0])))

        self.export_json(name, climbs)

    def export_json(self, name : str, data : list):
        path = name + '.json' if not name.endswith('.json') else ''
        with open(path, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)


def main(grade='v7'):
    with DBReader() as reader:
        reader.export_climbs('climbs_' + grade, reader.get_grade_from_string(grade))


if __name__ == '__main__':
    main()
else:
    main(sys.argv)