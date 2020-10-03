get_high_rollers="""
SELECT high_rollerid 
FROM high_roller_game
WHERE gameid = %(gameid)s
""",

add_pgid="""
INSERT INTO high_roller_game(high_rollerid,gameid,pgid,turn_pos,amount)
VALUES(%(high_rollerid)s,%(gameid)s,%(pgid)s,%(turn_pos)s,%(amount)s)
""",

remove_pgid="""
DELETE FROM high_roller_game
WHERE pgid = %(pgid)s
""",

get_pgid="""
SELECT * FROM high_roller_game
WHERE pgid = %(pgid)s
""",

remove_pgid_all="""
DELETE FROM high_roller_game
WHERE high_rollerid = %(high_rollerid)s
""",

add_card="""
INSERT INTO card(pgid,suit,rank)
VALUES(%(pgid)s,%(suit)s,%(rank)s)
""",

get_next_turn="""
SELECT turn_pos FROM high_roller_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos DESC
""",

get_ordered_turns="""
SELECT turn_pos FROM high_roller_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos ASC
""",

get_game_high_rollers="""
SELECT * FROM high_roller_game
WHERE gameid = %(gameid)s
""",

get_high_roller_cards="""
SELECT suit, rank FROM card
WHERE pgid = %(pgid)s
""",

check_for_pgid="""
SELECT pgid FROM high_roller_game
WHERE pgid = %(pgid)s
""",

create_game="""
INSERT INTO game(gameid,current_high_roller,game_state)
VALUES(%(gameid)s,1,'pregame')
""",

remove_game="""
DELETE FROM game
WHERE gameid = %(gameid)s
""",

remove_game_cards="""
DELETE FROM card as c
WHERE c.pgid IN (SELECT pg.pgid FROM high_roller_game AS pg
WHERE pg.gameid = %(gameid)s)
""",

check_for_game="""
SELECT * FROM game
WHERE gameid = %(gameid)s
""",

get_game="""
SELECT * FROM game
WHERE gameid = %(gameid)s
""",

get_current_games="""
SELECT * FROM high_roller_game
WHERE high_rollerid = %(high_rollerid)s
""",

get_game_state="""
SELECT game_state FROM game
WHERE gameid = %(gameid)s
""",

update_game_state="""
UPDATE game
SET game_state = %(game_state)s
WHERE gameid = %(gameid)s
""",

add_bet="""
UPDATE high_roller_game
SET amount = %(amount)s
WHERE pgid = %(pgid)s
""",

get_cards_in_play="""
SELECT pg.pgid,c.suit,c.rank FROM high_roller_game AS pg
INNER JOIN card AS c ON pg.pgid = c.pgid
WHERE pg.gameid = %(gameid)s
""",

assign_card="""
INSERT INTO card(pgid,suit,rank)
VALUES(%(pgid)s,%(suit)s,%(rank)s)
""",

get_turn_list="""
SELECT * FROM high_roller_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos ASC
""",

get_current_turn="""
SELECT current_high_roller FROM game
WHERE gameid = %(gameid)s
""",

set_turn="""
UPDATE game
SET current_high_roller = %(new_turn)s
WHERE gameid = %(gameid)s
""",

get_result_high_rollers="""
SELECT high_rollerid FROM high_roller_game
WHERE result = %(result)s AND gameid = %(gameid)s 
""",

update_high_roller_result="""
UPDATE high_roller_game
SET result = %(result)s
WHERE high_rollerid = %(high_rollerid)s
""",

get_result_bet="""
SELECT high_rollerid,amount FROM high_roller_game
WHERE result = %(result)s AND gameid = %(gameid)s
""",

get_high_roller_bet="""
SELECT amount FROM high_roller_game
WHERE pgid = %(pgid)s
"""