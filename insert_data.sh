#! /bin/bash

if [[ $1 == "test" ]]
then
  PSQL="psql --username=postgres --dbname=worldcuptest -t --no-align -c"
else
  PSQL="psql --username=freecodecamp --dbname=worldcup -t --no-align -c"
fi
# Xóa dữ liệu cũ
DEL_DATA=$($PSQL "truncate teams, games;")
if [[ $DEL_DATA == "TRUNCATE TABLE" ]]
then
  echo "Deleted all data from TEAMS and GAMES: Code result: $DEL_DATA"
fi
# Đọc file CSV, bỏ dòng tiêu đề
tail -n +2 games.csv | while IFS=',' read year round winner opponent winner_goals opponent_goals
do
  if [[ $year != "year" ]]; then

    # Làm sạch giá trị round nếu có ký tự đặc biệt
    round_clean=$(echo "$round" | sed 's/\xA0/ /g')

    # Thêm đội nếu chưa có
    for team in "$winner" "$opponent"
    do
      TEAM_ID=$($PSQL "select team_id from teams where name='$team';")
      if [[ -z $TEAM_ID ]]; then
        TEAM_ID_INSERT=$($PSQL "insert into teams(name) values('$team');")
        if [[ $TEAM_ID_INSERT == "INSERT 0 1" ]]; then
          echo "Added team $team"
        fi
      fi
    done

    # Lấy ID đội
    winnerID=$($PSQL "select team_id from teams where name='$winner';")
    opponentID=$($PSQL "select team_id from teams where name='$opponent';")

    # Thêm game
    ADD_GAME_RESULT=$($PSQL "insert into games(year, round, winner_id, opponent_id, winner_goals, opponent_goals) values($year, '$round_clean', $winnerID, $opponentID, $winner_goals, $opponent_goals);")
    if [[ $ADD_GAME_RESULT == "INSERT 0 1" ]]; then
      echo "Added game: $year | $round_clean | $winner vs $opponent ($winner_goals:$opponent_goals)"
    fi
  fi
done
# Do not change code above this line. Use the PSQL variable above to query your database.
