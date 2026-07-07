--
-- PostgreSQL database dump
--

\restrict tzgSNExnoWalfLiii9BQzxNDtfDnA0YzbGChzmnJdahhm5s68YSOSOuJGJzEwpd

-- Dumped from database version 18.2
-- Dumped by pg_dump version 18.2

-- Started on 2026-03-04 10:40:19

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
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 5077 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 222 (class 1259 OID 16597)
-- Name: anexos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anexos (
    id integer NOT NULL,
    nome text NOT NULL,
    predio_id integer
);


ALTER TABLE public.anexos OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16596)
-- Name: anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anexos_id_seq OWNER TO postgres;

--
-- TOC entry 5078 (class 0 OID 0)
-- Dependencies: 221
-- Name: anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anexos_id_seq OWNED BY public.anexos.id;


--
-- TOC entry 230 (class 1259 OID 16664)
-- Name: movimentacoes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movimentacoes (
    id integer NOT NULL,
    chave text NOT NULL,
    usuario text NOT NULL,
    data_retirada timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data_retorno timestamp without time zone,
    status text DEFAULT 'dispon¡vel'::text,
    email text,
    alerta_enviado boolean DEFAULT false,
    utilizador_id integer
);


ALTER TABLE public.movimentacoes OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16663)
-- Name: movimentacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movimentacoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimentacoes_id_seq OWNER TO postgres;

--
-- TOC entry 5079 (class 0 OID 0)
-- Dependencies: 229
-- Name: movimentacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movimentacoes_id_seq OWNED BY public.movimentacoes.id;


--
-- TOC entry 220 (class 1259 OID 16586)
-- Name: predios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.predios (
    id integer NOT NULL,
    nome text NOT NULL,
    endereco text
);


ALTER TABLE public.predios OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16585)
-- Name: predios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.predios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.predios_id_seq OWNER TO postgres;

--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 219
-- Name: predios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.predios_id_seq OWNED BY public.predios.id;


--
-- TOC entry 228 (class 1259 OID 16642)
-- Name: salas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.salas (
    id integer NOT NULL,
    nome text NOT NULL,
    descricao text,
    predio_id integer,
    anexo_id integer,
    status text DEFAULT 'disponivel'::text
);


ALTER TABLE public.salas OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16641)
-- Name: salas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.salas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.salas_id_seq OWNER TO postgres;

--
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 227
-- Name: salas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.salas_id_seq OWNED BY public.salas.id;


--
-- TOC entry 226 (class 1259 OID 16625)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    login text NOT NULL,
    nome text NOT NULL,
    senha text NOT NULL,
    primeiro_login boolean DEFAULT true,
    is_admin boolean DEFAULT false
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16624)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 225
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 224 (class 1259 OID 16613)
-- Name: utilizadores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.utilizadores (
    id integer NOT NULL,
    nome text NOT NULL,
    email text,
    ativo boolean DEFAULT true
);


ALTER TABLE public.utilizadores OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16612)
-- Name: utilizadores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.utilizadores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.utilizadores_id_seq OWNER TO postgres;

--
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 223
-- Name: utilizadores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.utilizadores_id_seq OWNED BY public.utilizadores.id;


--
-- TOC entry 4882 (class 2604 OID 16600)
-- Name: anexos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos ALTER COLUMN id SET DEFAULT nextval('public.anexos_id_seq'::regclass);


--
-- TOC entry 4890 (class 2604 OID 16667)
-- Name: movimentacoes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentacoes ALTER COLUMN id SET DEFAULT nextval('public.movimentacoes_id_seq'::regclass);


--
-- TOC entry 4881 (class 2604 OID 16589)
-- Name: predios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predios ALTER COLUMN id SET DEFAULT nextval('public.predios_id_seq'::regclass);


--
-- TOC entry 4888 (class 2604 OID 16645)
-- Name: salas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salas ALTER COLUMN id SET DEFAULT nextval('public.salas_id_seq'::regclass);


--
-- TOC entry 4885 (class 2604 OID 16628)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 4883 (class 2604 OID 16616)
-- Name: utilizadores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilizadores ALTER COLUMN id SET DEFAULT nextval('public.utilizadores_id_seq'::regclass);


--
-- TOC entry 5063 (class 0 OID 16597)
-- Dependencies: 222
-- Data for Name: anexos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.anexos (id, nome, predio_id) FROM stdin;
1	Anexo 1	1
2	Anexo 2	1
3	Anexo 3	1
\.


--
-- TOC entry 5071 (class 0 OID 16664)
-- Dependencies: 230
-- Data for Name: movimentacoes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movimentacoes (id, chave, usuario, data_retirada, data_retorno, status, email, alerta_enviado, utilizador_id) FROM stdin;
\.


--
-- TOC entry 5061 (class 0 OID 16586)
-- Dependencies: 220
-- Data for Name: predios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.predios (id, nome, endereco) FROM stdin;
1	Predio 1	
2	Predio 2	
\.


--
-- TOC entry 5069 (class 0 OID 16642)
-- Dependencies: 228
-- Data for Name: salas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.salas (id, nome, descricao, predio_id, anexo_id, status) FROM stdin;
2	201	Lab de Informatica	1	\N	disponivel
3	202	Lab de Informatica	1	\N	disponivel
4	102	Lab de Informatica	1	\N	disponivel
6	104	Assist Estudantil	1	\N	disponivel
7	105	Biblioteca	1	\N	disponivel
8	107	Regoistro Academico	1	\N	disponivel
9	106	Auditorio	1	\N	disponivel
10	111	Extensao	1	\N	disponivel
11	114	Atendimento Pisicop‚dagogico	1	\N	disponivel
12	116	NAPNE	1	\N	disponivel
13	117	Recursos Multifouncional	1	\N	disponivel
14	113	Recepcao	1	\N	disponivel
15	203	Equipe de higienizacao	1	\N	disponivel
16	204	Sala de comnvivencia	1	\N	disponivel
17	205	DAP / DI / Gabinete	1	\N	disponivel
18	206	Direcao Geral	1	\N	disponivel
19	207	Sala dos Professores	1	\N	disponivel
20	208	Sala de Reunioes	1	\N	disponivel
21	209	Coordenacoes de Cursos	1	\N	disponivel
23	210	Gestao de  Ensino	1	\N	disponivel
24	215	Lab de fotografia	1	\N	disponivel
25	216	Nnucleo de Audiovisual	1	\N	disponivel
26	01	Atelier	1	1	disponivel
27	02	Almoxerifado	1	1	disponivel
28	03	Sala de Cursos	1	1	disponivel
29	Container Gremiuo Estudantil	Container Gremiuo Estudantil	1	2	disponivel
30	Conatiner NPGES	Conatiner NPGES	1	2	disponivel
31	Sala de Educ Fisica	Sala de Educ Fisica	1	3	disponivel
32	Vestiario Feminino	Vestiario Feminino	1	3	disponivel
33	Vestiario Masculino	Vestiario Masculino	1	3	disponivel
34	Guarita / Portaria	Guarita / Portaria	1	\N	disponivel
35	CPD	CPD	1	\N	disponivel
36	01	Alvorada Maker	2	\N	disponivel
37	02	Estudio	2	\N	disponivel
38	03	Lab de Anbiente de Saude	2	\N	disponivel
39	04	Lab de Linguasgem (Musica)	2	\N	disponivel
40	05	Sala de Aula	2	\N	disponivel
41	06	Brinquedoteca	2	\N	disponivel
42	Quadra Poliesportiva	Quadra Poliesportiva	\N	\N	disponivel
43	101	\N	1	\N	disponivel
5	103	DTI	1	\N	disponivel
\.


--
-- TOC entry 5067 (class 0 OID 16625)
-- Dependencies: 226
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, login, nome, senha, primeiro_login, is_admin) FROM stdin;
1	admin	TIAlvorada	$2b$12$nzZo8DK0UNNfgSCJBKZabO8Erxfi0NaNMD89oXXtLLAhnyo71inEe	f	t
\.


--
-- TOC entry 5065 (class 0 OID 16613)
-- Dependencies: 224
-- Data for Name: utilizadores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.utilizadores (id, nome, email, ativo) FROM stdin;
\.


--
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 221
-- Name: anexos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.anexos_id_seq', 4, true);


--
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 229
-- Name: movimentacoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movimentacoes_id_seq', 1, false);


--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 219
-- Name: predios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.predios_id_seq', 3, true);


--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 227
-- Name: salas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.salas_id_seq', 1, true);


--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 225
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 1, false);


--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 223
-- Name: utilizadores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.utilizadores_id_seq', 1, false);


--
-- TOC entry 4897 (class 2606 OID 16606)
-- Name: anexos anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT anexos_pkey PRIMARY KEY (id);


--
-- TOC entry 4907 (class 2606 OID 16677)
-- Name: movimentacoes movimentacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentacoes
    ADD CONSTRAINT movimentacoes_pkey PRIMARY KEY (id);


--
-- TOC entry 4895 (class 2606 OID 16595)
-- Name: predios predios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predios
    ADD CONSTRAINT predios_pkey PRIMARY KEY (id);


--
-- TOC entry 4905 (class 2606 OID 16652)
-- Name: salas salas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_pkey PRIMARY KEY (id);


--
-- TOC entry 4901 (class 2606 OID 16640)
-- Name: usuarios usuarios_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_login_key UNIQUE (login);


--
-- TOC entry 4903 (class 2606 OID 16638)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4899 (class 2606 OID 16623)
-- Name: utilizadores utilizadores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.utilizadores
    ADD CONSTRAINT utilizadores_pkey PRIMARY KEY (id);


--
-- TOC entry 4908 (class 2606 OID 16607)
-- Name: anexos anexos_predio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos
    ADD CONSTRAINT anexos_predio_id_fkey FOREIGN KEY (predio_id) REFERENCES public.predios(id);


--
-- TOC entry 4911 (class 2606 OID 16683)
-- Name: movimentacoes fk_movimentacoes_utilizador; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentacoes
    ADD CONSTRAINT fk_movimentacoes_utilizador FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id) ON DELETE SET NULL;


--
-- TOC entry 4912 (class 2606 OID 16678)
-- Name: movimentacoes movimentacoes_utilizador_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentacoes
    ADD CONSTRAINT movimentacoes_utilizador_id_fkey FOREIGN KEY (utilizador_id) REFERENCES public.utilizadores(id);


--
-- TOC entry 4909 (class 2606 OID 16658)
-- Name: salas salas_anexo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_anexo_id_fkey FOREIGN KEY (anexo_id) REFERENCES public.anexos(id);


--
-- TOC entry 4910 (class 2606 OID 16653)
-- Name: salas salas_predio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_predio_id_fkey FOREIGN KEY (predio_id) REFERENCES public.predios(id);


-- Completed on 2026-03-04 10:40:19

--
-- PostgreSQL database dump complete
--

\unrestrict tzgSNExnoWalfLiii9BQzxNDtfDnA0YzbGChzmnJdahhm5s68YSOSOuJGJzEwpd

