-- Authoritative schema-only baseline from original project; no records or credentials.
CREATE TABLE public.deployment_logs (
    id integer NOT NULL,
    deployment_id integer,
    log_message text NOT NULL,
    log_level character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



CREATE SEQUENCE public.deployment_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.deployment_logs_id_seq OWNED BY public.deployment_logs.id;



CREATE TABLE public.deployments (
    id integer NOT NULL,
    repository_id integer,
    commit_id character varying(255),
    branch character varying(100),
    status character varying(50),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



CREATE SEQUENCE public.deployments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.deployments_id_seq OWNED BY public.deployments.id;



CREATE TABLE public.failure_analysis (
    id integer NOT NULL,
    deployment_id integer,
    failure_type character varying(100),
    error_message text,
    suggested_fix text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



CREATE SEQUENCE public.failure_analysis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.failure_analysis_id_seq OWNED BY public.failure_analysis.id;



CREATE TABLE public.repositories (
    id integer NOT NULL,
    user_id integer,
    name character varying(255) NOT NULL,
    url character varying(500),
    branch character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



CREATE SEQUENCE public.repositories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.repositories_id_seq OWNED BY public.repositories.id;



CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);



CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;



ALTER TABLE ONLY public.deployment_logs ALTER COLUMN id SET DEFAULT nextval('public.deployment_logs_id_seq'::regclass);



ALTER TABLE ONLY public.deployments ALTER COLUMN id SET DEFAULT nextval('public.deployments_id_seq'::regclass);



ALTER TABLE ONLY public.failure_analysis ALTER COLUMN id SET DEFAULT nextval('public.failure_analysis_id_seq'::regclass);



ALTER TABLE ONLY public.repositories ALTER COLUMN id SET DEFAULT nextval('public.repositories_id_seq'::regclass);



ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);



ALTER TABLE ONLY public.deployment_logs
    ADD CONSTRAINT deployment_logs_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.deployments
    ADD CONSTRAINT deployments_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.failure_analysis
    ADD CONSTRAINT failure_analysis_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.repositories
    ADD CONSTRAINT repositories_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);



ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);



ALTER TABLE ONLY public.deployment_logs
    ADD CONSTRAINT deployment_logs_deployment_id_fkey FOREIGN KEY (deployment_id) REFERENCES public.deployments(id);



ALTER TABLE ONLY public.deployments
    ADD CONSTRAINT deployments_repository_id_fkey FOREIGN KEY (repository_id) REFERENCES public.repositories(id);



ALTER TABLE ONLY public.failure_analysis
    ADD CONSTRAINT failure_analysis_deployment_id_fkey FOREIGN KEY (deployment_id) REFERENCES public.deployments(id);



ALTER TABLE ONLY public.repositories
    ADD CONSTRAINT repositories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);
