import math

# Spits out a bunch of info / stats for the tension board climbs SQLite Database
def output_stats(reader):

    print('Total Boulders: ', reader.db.execute('SELECT COUNT(uuid) FROM climbs LIMIT 1').fetchone()[0])
    print('Total Boulders (1+ ascents): ', reader.db.execute('SELECT COUNT(climb_uuid) FROM climb_stats LIMIT 1').fetchone()[0])
    print('Total Ascents: ', reader.db.execute('SELECT SUM(ascensionist_count) FROM climbs LIMIT 1').fetchone()[0])
    print('Total Setters: ', reader.db.execute('SELECT DISTINCT COUNT(setter_id) FROM climbs LIMIT 1').fetchone()[0])

    most_fa = reader.db.execute('''
        SELECT fa_username, COUNT(fa_username) AS occurrence 
        FROM climb_stats
        GROUP BY fa_username
        ORDER BY occurrence DESC
        LIMIT 1''').fetchone()
    print('Most First Ascents: {}, Count: {}'.format(most_fa[0],most_fa[1]))

    most_sets = reader.db.execute('''
        SELECT setter_username, COUNT(setter_id) AS occurrence 
        FROM climbs
        GROUP BY setter_id
        ORDER BY occurrence DESC
        LIMIT 1''').fetchone()
    print('Most Boulders from Setter: {}, Count: {}'.format(most_sets[0], most_sets[1]))

    average_grade = reader.db.execute('SELECT AVG(difficulty_average) FROM climb_stats LIMIT 1').fetchone()[0]
    print('Average Grade (Overall): {:.1f} ({})'.format(average_grade, reader.get_v_grade(int(average_grade))))
    print('Most Popular Boulder: ', reader.get_climb_row_info(reader.db.execute('''SELECT * FROM climbs ORDER BY ascensionist_count DESC LIMIT 1''').fetchone()))

    all_climbs = reader.db.execute('SELECT * FROM climbs WHERE ascensionist_count > 0').fetchall()
    max_ratings = max([x['ascensionist_count'] for x in all_climbs])
    global_rating = sum([x['quality_average'] for x in all_climbs]) / float(len(all_climbs))
    average_ascents = sum([x['ascensionist_count'] for x in all_climbs]) / float(len(all_climbs))
    print('Average Boulder Rating: {:.1f}, Average Ascents: {:.1f}'.format(global_rating, average_ascents))
    print('Highest Rated Boulder Wilson: ', reader.get_climb_row_info(max(all_climbs, key=lambda x: wilson_bound(x))))
    print('Highest Rated Boulder Bayesian: ', reader.get_climb_row_info(max(all_climbs, key=lambda x: bayesian_rating(x, max_ratings, 1.8))))
    print('Lowest Rated Climb Wilson: ', reader.get_climb_row_info(max(all_climbs, key=lambda x: wilson_bound(x, False))))
    print('Lowest Rated Climb Bayesian: ', reader.get_climb_row_info(min(all_climbs, key=lambda x: bayesian_rating(x, max_ratings, 1.8))))

    most_popular_query = '''
        SELECT placement_id, COUNT(placement_id) AS occurrence
        from climbs_placements
        INNER JOIN climbs on climb_uuid = uuid
        WHERE climbs.ascensionist_count > 0 {}
        GROUP BY placement_id
        ORDER BY occurrence DESC
        LIMIT 1'''
    find_hole_id = 'SELECT name from holes WHERE rowid=?'
    most_popular = reader.db.execute(most_popular_query.format('')).fetchone()[0]
    most_popular_start = reader.db.execute(most_popular_query.format('AND role_id=1')).fetchone()[0]
    most_popular_finish = reader.db.execute(most_popular_query.format('AND role_id=3')).fetchone()[0]
    print('Most Popular Hold: ', reader.db.execute(find_hole_id, (most_popular,)).fetchone()[0])
    print('Most Popular Start Hold: ', reader.db.execute(find_hole_id, (most_popular_start,)).fetchone()[0])
    print('Most Popular Finish Hold: ', reader.db.execute(find_hole_id, (most_popular_finish,)).fetchone()[0])

    for x in range(20, 55, 5):
        average = reader.db.execute('SELECT AVG(difficulty_average) FROM climb_stats WHERE angle=? LIMIT 1', (str(x),)).fetchone()[0]
        print('Average Grade ({} degrees): {:.1f} ({})'.format(x, average, reader.get_v_grade(int(average))))

    for x in range(0,17):
        v_grade = 'V' + str(x)
        climbs = reader.get_climbs_of_grade(v_grade)
        grade = reader.get_grade(v_grade)
        ascents = reader.db.execute('SELECT SUM(ascensionist_count) FROM climb_stats WHERE difficulty_average BETWEEN ? AND ? LIMIT 1', (grade[0], grade[-1])).fetchone()[0]
        print('{}: Boulders Count: {}, Ascents: {}'.format(v_grade, len(climbs), ascents))


# https://www.evanmiller.org/how-not-to-sort-by-average-rating.html
def wilson_bound(row, lower=True):
    n = row['ascensionist_count']
    pos = row['quality_average'] / 3.0 * n

    if not lower:
        pos = n - pos
    if n == 0:
        return 0
    z = 1.96
    phat = 1.0 * pos / n
    base = phat + z * z / (2 * n)
    ci = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)

    if not lower:
        ci = -ci

    return ( base - ci ) / (1 + z * z / n)

# https://math.stackexchange.com/questions/41459/how-can-i-calculate-most-popular-more-accurately/41513#41513
def bayesian_rating(row, max_ratings, global_average_rating):
    num_ratings = row['ascensionist_count']
    average_rating = row['quality_average']
    weight_factor = num_ratings / max_ratings
    return weight_factor * average_rating + (1.0 - weight_factor) * global_average_rating