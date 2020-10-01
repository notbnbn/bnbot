get_players="""
SELECT playerid 
FROM player_game
WHERE gameid = %(gameid)s
"""

add_pgid="""
INSERT INTO player_game(playerid,gameid,pgid,turn_pos,amount)
VALUES(%(playerid)s,%(gameid)s,%(pgid)s,%(turn_pos)s,%(amount)s)
"""

remove_pgid="""
DELETE FROM player_game
WHERE pgid = %(pgid)s
"""

get_pgid="""
SELECT * FROM player_game
WHERE pgid = %(pgid)s
"""

remove_pgid_all="""
DELETE FROM player_game
WHERE playerid = %(playerid)s
"""

add_card="""
INSERT INTO card(pgid,suit,rank)
VALUES(%(pgid)s,%(suit)s,%(rank)s)
"""

get_next_turn="""
SELECT turn_pos FROM player_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos DESC
"""

get_ordered_turns="""
SELECT turn_pos FROM player_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos ASC
"""

get_game_players="""
SELECT * FROM player_game
WHERE gameid = %(gameid)s
"""

get_player_cards="""
SELECT suit, rank FROM card
WHERE pgid = %(pgid)s
"""

check_for_pgid="""
SELECT pgid FROM player_game
WHERE pgid = %(pgid)s
"""

create_game="""
INSERT INTO game(gameid,current_player,game_state)
VALUES(%(gameid)s,1,'pregame')
"""

remove_game="""
DELETE FROM game
WHERE gameid = %(gameid)s
"""

remove_game_cards="""
DELETE FROM card as c
WHERE c.pgid IN (SELECT pg.pgid FROM player_game AS pg
WHERE pg.gameid = %(gameid)s)
"""

check_for_game="""
SELECT * FROM game
WHERE gameid = %(gameid)s
"""

get_game="""
SELECT * FROM game
WHERE gameid = %(gameid)s
"""

get_current_games="""
SELECT * FROM player_game
WHERE playerid = %(playerid)s
"""

get_game_state="""
SELECT game_state FROM game
WHERE gameid = %(gameid)s
"""

update_game_state="""
UPDATE game
SET game_state = %(game_state)s
WHERE gameid = %(gameid)s
"""

add_bet="""
UPDATE player_game
SET amount = %(amount)s
WHERE pgid = %(pgid)s
"""

get_cards_in_play="""
SELECT pg.pgid,c.suit,c.rank FROM player_game AS pg
INNER JOIN card AS c ON pg.pgid = c.pgid
WHERE pg.gameid = %(gameid)s
"""

assign_card="""
INSERT INTO card(pgid,suit,rank)
VALUES(%(pgid)s,%(suit)s,%(rank)s)
"""

get_turn_list="""
SELECT * FROM player_game
WHERE gameid = %(gameid)s
ORDER BY turn_pos ASC
"""

get_current_turn="""
SELECT current_player FROM game
WHERE gameid = %(gameid)s
"""

set_turn="""
UPDATE game
SET current_player = %(new_turn)s
WHERE gameid = %(gameid)s
"""

get_result_players="""
SELECT playerid FROM player_game
WHERE result = %(result)s AND gameid = %(gameid)s 
"""

update_player_result="""
UPDATE player_game
SET result = %(result)s
WHERE playerid = %(playerid)s
"""

get_result_bet="""
SELECT playerid,amount FROM player_game
WHERE result = %(result)s AND gameid = %(gameid)s
"""

get_player_bet="""
SELECT amount FROM player_game
WHERE pgid = %(pgid)s
"""