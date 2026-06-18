--
-- PostgreSQL database dump
--

\restrict 4vszAAnZUhEE1EKvIJ56fzB7xmnvRdq6enuZ7yogk8tkBLBupOEDE9J7zn4w4QK

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: Homework; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA "Homework";


ALTER SCHEMA "Homework" OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bot_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bot_settings (
    key text NOT NULL,
    value_int integer,
    last_update timestamp without time zone
);


ALTER TABLE public.bot_settings OWNER TO postgres;

--
-- Name: marriages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.marriages (
    id integer NOT NULL,
    user_one_id bigint,
    user_two_id bigint,
    chat_id bigint,
    married_at timestamp without time zone
);


ALTER TABLE public.marriages OWNER TO postgres;

--
-- Name: marriages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.marriages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.marriages_id_seq OWNER TO postgres;

--
-- Name: marriages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.marriages_id_seq OWNED BY public.marriages.id;


--
-- Name: medical_bans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_bans (
    user_id bigint NOT NULL,
    banned_until timestamp without time zone
);


ALTER TABLE public.medical_bans OWNER TO postgres;

--
-- Name: medical_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_questions (
    id integer NOT NULL,
    user_id bigint,
    question_text text,
    created_at timestamp without time zone,
    chat_id bigint
);


ALTER TABLE public.medical_questions OWNER TO postgres;

--
-- Name: medical_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medical_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_questions_id_seq OWNER TO postgres;

--
-- Name: medical_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medical_questions_id_seq OWNED BY public.medical_questions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    username text,
    custom_nickname text,
    rating integer DEFAULT 0,
    registered_at timestamp without time zone DEFAULT CURRENT_DATE,
    rang text DEFAULT 'Рекрут I'::text,
    last_r34_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: marriages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marriages ALTER COLUMN id SET DEFAULT nextval('public.marriages_id_seq'::regclass);


--
-- Name: medical_questions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_questions ALTER COLUMN id SET DEFAULT nextval('public.medical_questions_id_seq'::regclass);


--
-- Name: bot_settings bot_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bot_settings
    ADD CONSTRAINT bot_settings_pkey PRIMARY KEY (key);


--
-- Name: marriages marriages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.marriages
    ADD CONSTRAINT marriages_pkey PRIMARY KEY (id);


--
-- Name: medical_bans medical_bans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_bans
    ADD CONSTRAINT medical_bans_pkey PRIMARY KEY (user_id);


--
-- Name: medical_questions medical_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_questions
    ADD CONSTRAINT medical_questions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 4vszAAnZUhEE1EKvIJ56fzB7xmnvRdq6enuZ7yogk8tkBLBupOEDE9J7zn4w4QK

