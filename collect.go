package main

import (
	"database/sql"
	"encoding/json"
	_ "github.com/mattn/go-sqlite3"
	"log"
	"time"
)

const StatDB string = "stat.db"
const TrafficDB string = "/etc/x-ui/x-ui.db"

type Email string
type AllTime int
type Nickname string

var clientTraffics = make(map[Email]AllTime)
var inbounds = make(map[Nickname]Email)

func main() {
	read()
	write()
}

func read() {
	log.Print("reading")
	defer func() { log.Print("end reading") }()

	db, err := sql.Open("sqlite3", TrafficDB)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	readClientTraffics(db)
	readInbounds(db)
}

func readClientTraffics(db *sql.DB) {
	log.Print("reading client traffics")
	defer func() { log.Print("end reading client traffics") }()

	rows, err := db.Query("select email, all_time from client_traffics")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()
	for rows.Next() {
		var email Email
		var allTime AllTime
		err = rows.Scan(&email, &allTime)
		if err != nil {
			log.Fatal(err)
			continue
		}
		clientTraffics[email] = allTime
	}
	err = rows.Err()
	if err != nil {
		log.Fatal(err)
	}
}

func readInbounds(db *sql.DB) {
	log.Print("reading inbounds")
	defer func() { log.Print("end reading inbounds") }()

	rows, err := db.Query("select remark, settings from inbounds")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var nickname Nickname
		var settings string

		err = rows.Scan(&nickname, &settings)
		if err != nil {
			log.Fatal(err)
		}

		var settingsParsed struct {
			Clients []struct {
				Email Email `json:"email"`
			} `json:"clients"`
		}
		err = json.Unmarshal([]byte(settings), &settingsParsed)
		if err != nil {
			log.Fatal(err)
		}

		inbounds[nickname] = settingsParsed.Clients[0].Email
	}

	err = rows.Err()
	if err != nil {
		log.Fatal(err)
	}
}

func write() {
	log.Print("writing")
	defer func() { log.Print("end writing") }()
	// year, month, day := time.Now().Day()
	// hh, mm, ss := time.Now().Clock()
	// fmt.Println(hh, mm, ss)

	db, err := sql.Open("sqlite3", StatDB)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	var stmt string
	stmt = `create table if not exists stat (
id integer not null primary key autoincrement,
year int,
month int,
day int,
nickname text,
alltime int
)`
	_, err = db.Exec(stmt)
	if err != nil {
		log.Printf("%q: %s\n", err, stmt)
		return
	}

	{
		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		stmt, err := tx.Prepare("insert into stat(year, month, day, nickname, alltime) values (?, ?, ?, ?, ?)")
		if err != nil {
			log.Fatal(err)
		}
		year, month, day := time.Now().Date()
		for nickname, email := range inbounds {
			var alltime AllTime
			alltime = clientTraffics[email]
			_, err = stmt.Exec(year, month, day, nickname, alltime)
			if err != nil {
				log.Fatal(err)
			}

		}
		err = tx.Commit()
		if err != nil {
			log.Fatal(err)
		}
	}
}
