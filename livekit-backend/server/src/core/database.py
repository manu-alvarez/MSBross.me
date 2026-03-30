"""
MSB Restaurant Reservation System — Database Module

SQLite database for managing restaurant tables, reservations,
configuration, call history and AI pipeline profiles.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger("msb-assistant")

# Dynamic database path (supports Local and VPS)
# __file__ is /server/src/core/database.py -> we need /server/data/restaurant.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "restaurant.db")
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

logger.info(f"Database module charging. Path: {DB_PATH}")


class RestaurantDB:
    """SQLite-backed restaurant reservation and AI pipeline database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _safe_add_column(self, conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        except sqlite3.OperationalError:
            pass

    def _init_db(self) -> None:
        """Create tables and seed defaults when database is new."""
        conn = self._get_conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS restaurant_info (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    cuisine_type TEXT DEFAULT '',
                    opening_time_lunch TEXT DEFAULT '13:00',
                    closing_time_lunch TEXT DEFAULT '16:00',
                    opening_time_dinner TEXT DEFAULT '20:00',
                    closing_time_dinner TEXT DEFAULT '23:30',
                    days_open TEXT DEFAULT 'lunes,martes,miercoles,jueves,viernes,sabado',
                    days_closed TEXT DEFAULT 'domingo',
                    reservation_slot_minutes INTEGER DEFAULT 30,
                    max_party_size INTEGER DEFAULT 10,
                    special_notes TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_number INTEGER NOT NULL UNIQUE,
                    capacity INTEGER NOT NULL,
                    location TEXT DEFAULT 'interior',
                    is_active BOOLEAN DEFAULT 1,
                    description TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT DEFAULT '',
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    num_guests INTEGER NOT NULL,
                    table_id INTEGER,
                    status TEXT DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled','completed','no_show')),
                    notes TEXT DEFAULT '',
                    source TEXT DEFAULT 'phone' CHECK(source IN ('phone','web','dashboard','walk_in')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES tables(id)
                );

                CREATE TABLE IF NOT EXISTS call_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caller_id TEXT DEFAULT '',
                    room_name TEXT DEFAULT '',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER DEFAULT 0,
                    result TEXT DEFAULT 'unknown' CHECK(result IN (
                        'reservation_created','reservation_cancelled',
                        'info_request','no_action','unknown'
                    )),
                    summary TEXT DEFAULT '',
                    transcription TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS llm_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    model_name TEXT NOT NULL,
                    voice TEXT NOT NULL,
                    temperature REAL DEFAULT 0.7,
                    system_prompt TEXT NOT NULL,
                    enable_internet_search BOOLEAN DEFAULT 0,
                    vad_sensitivity REAL DEFAULT 0.5,
                    turn_detection_mode TEXT DEFAULT 'normal',
                    max_call_duration_minutes INTEGER DEFAULT 30,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS pipeline_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    architecture TEXT NOT NULL DEFAULT 'realtime' CHECK(architecture IN ('realtime','modular')),
                    llm_provider TEXT NOT NULL DEFAULT 'ollama',
                    llm_model TEXT,
                    llm_base_url TEXT,
                    llm_temperature REAL DEFAULT 0.7,
                    stt_provider TEXT NOT NULL DEFAULT 'faster-whisper',
                    stt_model TEXT DEFAULT 'base',
                    stt_language TEXT DEFAULT 'auto',
                    stt_server_url TEXT,
                    tts_provider TEXT NOT NULL DEFAULT 'kokoro',
                    tts_voice TEXT DEFAULT 'af_heart',
                    tts_speed REAL DEFAULT 1.0,
                    tts_server_url TEXT,
                    realtime_provider TEXT NOT NULL DEFAULT 'gemini',
                    realtime_model TEXT,
                    realtime_voice TEXT DEFAULT 'Aoede',
                    google_stt_model TEXT DEFAULT 'gemini-1.5-flash',
                    google_tts_voice TEXT DEFAULT 'Aoede',
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'principal' CHECK(category IN (
                        'entrante','principal','postre','bebida','tapa','especial'
                    )),
                    price REAL DEFAULT 0.0,
                    allergens TEXT DEFAULT '',
                    is_available BOOLEAN DEFAULT 1,
                    is_daily_special BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(date);
                CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);
                CREATE INDEX IF NOT EXISTS idx_call_log_started ON call_log(started_at);
                CREATE INDEX IF NOT EXISTS idx_pipeline_configs_active ON pipeline_configs(is_active);
                CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
                """
            )

            # Backward compatible migrations for llm_config
            self._safe_add_column(conn, "llm_config", "enable_internet_search", "BOOLEAN DEFAULT 0")
            self._safe_add_column(conn, "llm_config", "vad_sensitivity", "REAL DEFAULT 0.5")
            self._safe_add_column(conn, "llm_config", "turn_detection_mode", "TEXT DEFAULT 'normal'")
            self._safe_add_column(conn, "llm_config", "max_call_duration_minutes", "INTEGER DEFAULT 30")

            # Backward compatible migrations for pipeline_configs
            self._safe_add_column(conn, "pipeline_configs", "stt_server_url", "TEXT")
            self._safe_add_column(conn, "pipeline_configs", "realtime_voice", "TEXT DEFAULT 'Aoede'")
            self._safe_add_column(conn, "pipeline_configs", "google_stt_model", "TEXT DEFAULT 'gemini-1.5-flash'")
            self._safe_add_column(conn, "pipeline_configs", "google_tts_voice", "TEXT DEFAULT 'Aoede'")

            # Seed restaurant
            if conn.execute("SELECT COUNT(*) AS c FROM restaurant_info").fetchone()["c"] == 0:
                conn.execute(
                    """
                    INSERT INTO restaurant_info (id, name, address, phone, description, cuisine_type)
                    VALUES (
                        1,
                        'Restaurante MSB',
                        'Calle Principal 1, Madrid',
                        '621322300',
                        'Restaurante de cocina mediterránea con ambiente acogedor.',
                        'Mediterránea'
                    )
                    """
                )
                logger.info("Seeded default restaurant info")

            # Seed tables
            if conn.execute("SELECT COUNT(*) AS c FROM tables").fetchone()["c"] == 0:
                default_tables = [
                    (1, 2, "interior", "Mesa junto a la ventana"),
                    (2, 2, "interior", "Mesa de pareja"),
                    (3, 4, "interior", "Mesa familiar"),
                    (4, 4, "interior", "Mesa central"),
                    (5, 4, "terraza", "Mesa terraza cubierta"),
                    (6, 6, "interior", "Mesa grupo grande"),
                    (7, 6, "terraza", "Mesa terraza grupo"),
                    (8, 8, "privado", "Reservado privado"),
                ]
                conn.executemany(
                    "INSERT INTO tables (table_number, capacity, location, description) VALUES (?, ?, ?, ?)",
                    default_tables,
                )
                logger.info("Seeded %d default tables", len(default_tables))

            # Seed llm config
            if conn.execute("SELECT COUNT(*) AS c FROM llm_config").fetchone()["c"] == 0:
                default_prompt = (
                    "Eres el asistente telefónico automático del {restaurant_name}. "
                    "Tu trabajo es ayudar a los clientes a hacer reservas, responder preguntas "
                    "sobre el horario, la dirección y la capacidad."
                )
                conn.execute(
                    """
                    INSERT INTO llm_config (
                        id, model_name, voice, temperature, system_prompt,
                        enable_internet_search, vad_sensitivity, turn_detection_mode, max_call_duration_minutes
                    )
                    VALUES (1, 'gemini-1.5-flash', 'Aoede', 0.7, ?, 0, 0.5, 'normal', 30)
                    """,
                    (default_prompt,),
                )
                logger.info("Seeded default LLM config")

            # Seed menu items
            if conn.execute("SELECT COUNT(*) AS c FROM menu_items").fetchone()["c"] == 0:
                default_menu = [
                    ('Ensalada Mediterránea', 'Tomate, pepino, aceitunas, queso feta y vinagreta de limón', 'entrante', 9.50, 'lácteos', 1, 0),
                    ('Croquetas de Jamón Ibérico', 'Croquetas caseras crujientes con bechamel suave', 'entrante', 8.00, 'gluten,lácteos', 1, 0),
                    ('Gazpacho Andaluz', 'Sopa fría de tomate, pimiento y pepino', 'entrante', 7.00, '', 1, 0),
                    ('Lubina a la Plancha', 'Lubina fresca con verduras de temporada y aceite de oliva virgen', 'principal', 18.50, 'pescado', 1, 0),
                    ('Paella Valenciana', 'Arroz con pollo, judías verdes, garrofón y azafrán', 'principal', 16.00, '', 1, 0),
                    ('Solomillo de Ternera', 'Solomillo con reducción de Pedro Ximénez y patatas al horno', 'principal', 22.00, '', 1, 0),
                    ('Risotto de Setas', 'Arroz cremoso con setas de temporada y parmesano', 'principal', 14.50, 'lácteos,gluten', 1, 0),
                    ('Tiramisú Casero', 'Bizcocho de café con mascarpone y cacao', 'postre', 7.50, 'gluten,lácteos,huevo', 1, 0),
                    ('Tarta de Queso', 'Tarta horneada con base de galleta y coulis de frutos rojos', 'postre', 7.00, 'gluten,lácteos,huevo', 1, 0),
                    ('Sangría de la Casa', 'Vino tinto con frutas de temporada y especias', 'bebida', 5.00, '', 1, 0),
                    ('Agua Mineral', 'Botella 750ml', 'bebida', 2.50, '', 1, 0),
                ]
                conn.executemany(
                    "INSERT INTO menu_items (name, description, category, price, allergens, is_available, is_daily_special) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    default_menu,
                )
                logger.info("Seeded %d default menu items", len(default_menu))

            # Seed pipeline profiles
            if conn.execute("SELECT COUNT(*) AS c FROM pipeline_configs").fetchone()["c"] == 0:
                conn.executemany(
                    """
                    INSERT INTO pipeline_configs (
                        name, architecture, llm_provider, llm_model, llm_base_url, llm_temperature,
                        stt_provider, stt_model, stt_language, stt_server_url,
                        tts_provider, tts_voice, tts_speed, tts_server_url,
                        realtime_provider, realtime_model, realtime_voice,
                        google_stt_model, google_tts_voice, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "Gemini 2.5 Flash Native Audio",
                            "realtime",
                            "gemini",
                            "gemini-2.5-flash-native-audio-latest",
                            None,
                            0.7,
                            "google-stt",
                            "gemini-2.5-flash-native-audio-latest",
                            "es",
                            None,
                            "google-tts",
                            "Aoede",
                            1.0,
                            None,
                            "gemini",
                            "gemini-2.5-flash-native-audio-latest",
                            "Aoede",
                            "gemini-2.5-flash-native-audio-latest",
                            "Aoede",
                            1,
                        ),
                        (
                            "Gemini 1.5 Native Realtime (Flash-8B)",
                            "realtime",
                            "gemini",
                            "gemini-1.5-flash-8b",
                            None,
                            0.7,
                            "google-stt",
                            "gemini-1.5-flash-8b",
                            "es",
                            None,
                            "google-tts",
                            "Puck",
                            1.0,
                            None,
                            "gemini",
                            "gemini-1.5-flash-8b",
                            "Puck",
                            "gemini-1.5-flash-8b",
                            "Puck",
                            0,
                        ),
                        (
                            "Gemini 1.5 Realtime (Flash)",
                            "realtime",
                            "gemini",
                            "gemini-1.5-flash",
                            None,
                            0.7,
                            "google-stt",
                            "gemini-1.5-flash",
                            "es",
                            None,
                            "google-tts",
                            "Puck",
                            1.0,
                            None,
                            "gemini",
                            "gemini-1.5-flash",
                            "Puck",
                            "gemini-1.5-flash",
                            "Puck",
                            0,
                        ),
                        (
                            "Local Modular",
                            "modular",
                            "gemini",
                            "gemini-1.5-flash",
                            None,
                            0.7,
                            "faster-whisper",
                            "base",
                            "es",
                            "http://localhost:8178",
                            "kokoro-82m",
                            "af_heart",
                            1.0,
                            "http://localhost:8880",
                            "gemini",
                            "gemini-1.5-flash",
                            "Aoede",
                            "gemini-1.5-flash",
                            "Aoede",
                            0,
                        ),
                    ],
                )
                logger.info("Seeded default pipeline profiles")

            # Migration: Add Gemini 2.5 to EXISTING databases that don't have it yet
            existing_25 = conn.execute(
                "SELECT 1 FROM pipeline_configs WHERE realtime_model = 'gemini-2.5-flash-native-audio-latest'"
            ).fetchone()
            if not existing_25:
                conn.execute(
                    """
                    INSERT INTO pipeline_configs (
                        name, architecture, llm_provider, llm_model, llm_base_url, llm_temperature,
                        stt_provider, stt_model, stt_language, stt_server_url,
                        tts_provider, tts_voice, tts_speed, tts_server_url,
                        realtime_provider, realtime_model, realtime_voice,
                        google_stt_model, google_tts_voice, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Gemini 2.5 Flash Native Audio",
                        "realtime",
                        "gemini",
                        "gemini-2.5-flash-native-audio-latest",
                        None,
                        0.7,
                        "google-stt",
                        "gemini-2.5-flash-native-audio-latest",
                        "es",
                        None,
                        "google-tts",
                        "Aoede",
                        1.0,
                        None,
                        "gemini",
                        "gemini-2.5-flash-native-audio-latest",
                        "Aoede",
                        "gemini-2.5-flash-native-audio-latest",
                        "Aoede",
                        0,
                    ),
                )
                logger.info("Migration: Added Gemini 2.5 Flash Native Audio pipeline")

            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Restaurant Info
    # ------------------------------------------------------------------

    def get_restaurant_info(self) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM restaurant_info WHERE id = 1").fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def update_restaurant_info(self, **kwargs) -> None:
        allowed = {
            "name",
            "address",
            "phone",
            "description",
            "cuisine_type",
            "opening_time_lunch",
            "closing_time_lunch",
            "opening_time_dinner",
            "closing_time_dinner",
            "days_open",
            "days_closed",
            "reservation_slot_minutes",
            "max_party_size",
            "special_notes",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values())
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE restaurant_info SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # LLM Config
    # ------------------------------------------------------------------

    def get_llm_config(self) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM llm_config WHERE id = 1").fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def update_llm_config(self, **kwargs) -> None:
        allowed = {
            "model_name",
            "voice",
            "temperature",
            "system_prompt",
            "enable_internet_search",
            "vad_sensitivity",
            "turn_detection_mode",
            "max_call_duration_minutes",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values())
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE llm_config SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Pipeline Config
    # ------------------------------------------------------------------

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict:
        return dict(row) if row else {}

    def get_pipeline_config(self, config_id: int) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM pipeline_configs WHERE id = ?",
                (config_id,),
            ).fetchone()
            return self._row_to_dict(row)
        finally:
            conn.close()

    def get_active_pipeline_config(self) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM pipeline_configs WHERE is_active = 1 ORDER BY id ASC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)

            # Fallback for legacy DBs with no active profile
            row = conn.execute("SELECT * FROM pipeline_configs ORDER BY id ASC LIMIT 1").fetchone()
            if row:
                conn.execute("UPDATE pipeline_configs SET is_active = 1 WHERE id = ?", (row["id"],))
                conn.commit()
                return dict(row)
            return {}
        finally:
            conn.close()

    def list_pipeline_configs(self) -> list[dict]:
        conn = self._get_conn()
        try:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM pipeline_configs ORDER BY is_active DESC, id ASC"
                ).fetchall()
            ]
        finally:
            conn.close()

    def update_pipeline_config(self, config_id: int, **kwargs) -> dict:
        allowed = {
            "name",
            "architecture",
            "llm_provider",
            "llm_model",
            "llm_base_url",
            "llm_temperature",
            "stt_provider",
            "stt_model",
            "stt_language",
            "stt_server_url",
            "tts_provider",
            "tts_voice",
            "tts_speed",
            "tts_server_url",
            "realtime_provider",
            "realtime_model",
            "realtime_voice",
            "google_stt_model",
            "google_tts_voice",
            "is_active",
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return self.get_pipeline_config(config_id)

        conn = self._get_conn()
        try:
            if fields.get("is_active"):
                conn.execute("UPDATE pipeline_configs SET is_active = 0")

            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [config_id]
            conn.execute(
                f"UPDATE pipeline_configs SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )
            conn.commit()
        finally:
            conn.close()
        return self.get_pipeline_config(config_id)

    def activate_pipeline(self, config_id: int) -> bool:
        conn = self._get_conn()
        try:
            exists = conn.execute(
                "SELECT 1 FROM pipeline_configs WHERE id = ?",
                (config_id,),
            ).fetchone()
            if not exists:
                return False
            conn.execute("UPDATE pipeline_configs SET is_active = 0")
            conn.execute(
                "UPDATE pipeline_configs SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (config_id,),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    def get_tables(self, active_only: bool = True) -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM tables"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY table_number"
            return [dict(r) for r in conn.execute(query).fetchall()]
        finally:
            conn.close()

    def create_table(
        self,
        table_number: int,
        capacity: int,
        location: str = "interior",
        description: str = "",
    ) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO tables (table_number, capacity, location, description) VALUES (?, ?, ?, ?)",
                (table_number, capacity, location, description),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_table(self, table_id: int, **kwargs) -> None:
        allowed = {"table_number", "capacity", "location", "is_active", "description"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [table_id]
        conn = self._get_conn()
        try:
            conn.execute(f"UPDATE tables SET {set_clause} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()

    def delete_table(self, table_id: int) -> None:
        self.update_table(table_id, is_active=0)

    # ------------------------------------------------------------------
    # Reservations
    # ------------------------------------------------------------------

    def check_availability(self, date: str, time: str, num_guests: int) -> list[dict]:
        conn = self._get_conn()
        try:
            info = dict(conn.execute("SELECT * FROM restaurant_info WHERE id = 1").fetchone())
            slot_minutes = info.get("reservation_slot_minutes", 30)

            query = """
                SELECT t.* FROM tables t
                WHERE t.is_active = 1
                  AND t.capacity >= ?
                  AND t.id NOT IN (
                      SELECT r.table_id FROM reservations r
                      WHERE r.date = ?
                        AND r.status = 'confirmed'
                        AND r.table_id IS NOT NULL
                        AND (
                            (r.time <= ? AND time(r.time, '+' || ? || ' minutes') > ?)
                            OR (r.time < time(?, '+' || ? || ' minutes') AND r.time >= ?)
                        )
                  )
                ORDER BY t.capacity ASC, t.table_number ASC
            """
            rows = conn.execute(
                query,
                (num_guests, date, time, slot_minutes, time, time, slot_minutes, time),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def create_reservation(
        self,
        customer_name: str,
        date: str,
        time: str,
        num_guests: int,
        customer_phone: str = "",
        notes: str = "",
        source: str = "phone",
    ) -> dict:
        available = self.check_availability(date, time, num_guests)
        if not available:
            raise ValueError(
                f"No tables available for {num_guests} guests on {date} at {time}."
            )

        best_table = available[0]
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                INSERT INTO reservations
                (customer_name, customer_phone, date, time, num_guests, table_id, notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_name,
                    customer_phone,
                    date,
                    time,
                    num_guests,
                    best_table["id"],
                    notes,
                    source,
                ),
            )
            conn.commit()
            reservation_id = cursor.lastrowid
            return {
                "reservation_id": reservation_id,
                "customer_name": customer_name,
                "date": date,
                "time": time,
                "num_guests": num_guests,
                "table_number": best_table["table_number"],
                "table_location": best_table["location"],
                "status": "confirmed",
            }
        finally:
            conn.close()

    def cancel_reservation(
        self,
        reservation_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
    ) -> bool:
        conn = self._get_conn()
        try:
            if reservation_id:
                cursor = conn.execute(
                    "UPDATE reservations SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ? AND status = 'confirmed'",
                    (reservation_id,),
                )
            elif customer_name and customer_phone:
                cursor = conn.execute(
                    "UPDATE reservations SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
                    "WHERE customer_name = ? AND customer_phone = ? AND status = 'confirmed' "
                    "AND date >= date('now')",
                    (customer_name, customer_phone),
                )
            elif customer_name:
                cursor = conn.execute(
                    "UPDATE reservations SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ("
                    "  SELECT id FROM reservations "
                    "  WHERE customer_name = ? AND status = 'confirmed' "
                    "  AND date >= date('now') "
                    "  ORDER BY date ASC, time ASC LIMIT 1"
                    ")",
                    (customer_name,),
                )
            else:
                return False

            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_reservations(self, date: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        conn = self._get_conn()
        try:
            query = """
                SELECT r.*, t.table_number, t.capacity, t.location AS table_location
                FROM reservations r
                LEFT JOIN tables t ON r.table_id = t.id
                WHERE 1=1
            """
            params: list[str] = []
            if date:
                query += " AND r.date = ?"
                params.append(date)
            if status:
                query += " AND r.status = ?"
                params.append(status)
            query += " ORDER BY r.date ASC, r.time ASC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]
        finally:
            conn.close()

    def find_reservations_by_phone(self, phone: str) -> list[dict]:
        conn = self._get_conn()
        try:
            query = """
                SELECT r.*, t.table_number, t.location AS table_location
                FROM reservations r
                LEFT JOIN tables t ON r.table_id = t.id
                WHERE r.customer_phone LIKE ? AND r.status = 'confirmed' AND r.date >= date('now')
                ORDER BY r.date ASC, r.time ASC
            """
            return [dict(r) for r in conn.execute(query, (f"%{phone}%",)).fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Call Log
    # ------------------------------------------------------------------

    def log_call(
        self,
        caller_id: str = "",
        room_name: str = "",
        result: str = "unknown",
        summary: str = "",
        transcription: str = "",
        duration_seconds: int = 0,
    ) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                INSERT INTO call_log (caller_id, room_name, result, summary, transcription, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (caller_id, room_name, result, summary, transcription, duration_seconds),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_call_log(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        try:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM call_log ORDER BY started_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            ]
        finally:
            conn.close()

    def get_recent_calls(self, minutes: int = 60) -> list[dict]:
        """Get calls from the last N minutes for short-term memory injection."""
        conn = self._get_conn()
        try:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM call_log WHERE started_at >= datetime('now', ? || ' minutes') ORDER BY started_at DESC",
                    (f"-{minutes}",),
                ).fetchall()
            ]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self, date: Optional[str] = None) -> dict:
        conn = self._get_conn()
        try:
            date = date or datetime.now().strftime("%Y-%m-%d")

            today_res = conn.execute(
                "SELECT COUNT(*) AS c FROM reservations WHERE date = ? AND status = 'confirmed'",
                (date,),
            ).fetchone()
            total_guests = conn.execute(
                "SELECT COALESCE(SUM(num_guests), 0) AS s FROM reservations WHERE date = ? AND status = 'confirmed'",
                (date,),
            ).fetchone()
            total_tables = conn.execute(
                "SELECT COUNT(*) AS c FROM tables WHERE is_active = 1"
            ).fetchone()
            cancelled = conn.execute(
                "SELECT COUNT(*) AS c FROM reservations WHERE date = ? AND status = 'cancelled'",
                (date,),
            ).fetchone()

            # New: Global stats to show activity even if today is empty
            total_reservations = conn.execute(
                "SELECT COUNT(*) AS c FROM reservations"
            ).fetchone()
            next_7_days = conn.execute(
                "SELECT COUNT(*) AS c FROM reservations WHERE date >= ? AND date <= date(?, '+7 days') AND status = 'confirmed'",
                (date, date),
            ).fetchone()
            total_calls = conn.execute(
                "SELECT COUNT(*) AS c FROM call_log"
            ).fetchone()

            return {
                "date": date,
                "reservations_today": today_res["c"],
                "guests_today": total_guests["s"],
                "total_tables": total_tables["c"],
                "cancellations_today": cancelled["c"],
                "total_reservations": total_reservations["c"],
                "reservations_next_7_days": next_7_days["c"],
                "total_calls": total_calls["c"],
            }
        finally:
            conn.close()


    # ------------------------------------------------------------------
    # Menu Items
    # ------------------------------------------------------------------

    def get_menu(self, category: Optional[str] = None, available_only: bool = True) -> list[dict]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM menu_items WHERE 1=1"
            params: list = []
            if available_only:
                query += " AND is_available = 1"
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY category, name"
            return [dict(r) for r in conn.execute(query, params).fetchall()]
        finally:
            conn.close()

    def create_menu_item(self, name: str, description: str, category: str, price: float,
                         allergens: str = "", is_available: bool = True, is_daily_special: bool = False) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "INSERT INTO menu_items (name, description, category, price, allergens, is_available, is_daily_special) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, description, category, price, allergens, int(is_available), int(is_daily_special)),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_menu_item(self, item_id: int, **kwargs) -> None:
        allowed = {"name", "description", "category", "price", "allergens", "is_available", "is_daily_special"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [item_id]
        conn = self._get_conn()
        try:
            conn.execute(f"UPDATE menu_items SET {set_clause} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()

    def delete_menu_item(self, item_id: int) -> None:
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
            conn.commit()
        finally:
            conn.close()


# Singleton instance
db = RestaurantDB()
