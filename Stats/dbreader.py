import sqlite3, json, sys, atexit
import stats

ENABLE_DEBUG_LOGGING = False

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

    def get_grade_row(self, grade : str) -> list:
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
        return grade_results

    def get_grade(self, grade : str) -> list:
        return [x[0] for x in self.get_grade_row(grade)]

    def get_v_grade(self, grade : str) -> list:
        return self.get_grade_row(grade)[0]['verm_name']

    def get_climbs_of_grade(self, grade : list, min_rating=0.0):
        command = '''
            SELECT name 
            FROM climbs
            INNER JOIN climb_stats on climb_stats.climb_uuid = climbs.uuid
            WHERE climb_stats.difficulty_average BETWEEN ? AND ? 
            AND climb_stats.quality_average >= ?
            ORDER BY climb_stats.quality_average
        '''         
        grade = self.get_grade(grade)
        climbs = self.db.execute(command, (grade[0], grade[-1], min_rating)).fetchall()

        if ENABLE_DEBUG_LOGGING:
            print('{} climbs found at grade {}'.format(len(climbs), '{} to {}'.format(grade[0], grade[-1]) if len(grade) > 1 else str(grade[0])))
        return climbs

    def get_climb_row_info(self, climb):
        return '{}, Grade: {}, Ascents: {}, Setter: {}, FA: {}, Rating: {:.1f}'.format(
            climb['name'], 
            self.get_v_grade(int(climb['difficulty_average'])), 
            climb['ascensionist_count'], 
            climb['setter_username'], 
            self.db.execute('SELECT fa_username from climb_stats WHERE climb_uuid=?', (climb['uuid'],)).fetchone()[0],
            climb['quality_average'])

    def export_climbs(self, name : str, grade : list, rating=None):
        climbs = self.get_climbs_of_grade(grade,rating)
        self.export_json(name, climbs)

    def export_json(self, name : str, data : list):
        path = name + '.json' if not name.endswith('.json') else ''
        with open(path, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)

    def output_stats(self):
        stats.output_stats(self)


def main(grade='v7'):
    with DBReader() as reader:
        #reader.export_climbs('climbs_' + grade, reader.get_grade_from_string(grade))
        reader.output_stats()


if __name__ == '__main__':
    main()
else:
    main(sys.argv)