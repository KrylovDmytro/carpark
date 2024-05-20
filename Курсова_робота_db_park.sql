PGDMP      :                |        
   db_carpark    16.3    16.3 E               0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            	           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            
           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false                       1262    16398 
   db_carpark    DATABASE     ~   CREATE DATABASE db_carpark WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
    DROP DATABASE db_carpark;
                postgres    false            �            1255    33153 /   add_or_update_payment_method(character varying) 	   PROCEDURE     a  CREATE PROCEDURE public.add_or_update_payment_method(IN p_payment_card character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if the payment method exists
    IF EXISTS (SELECT 1 FROM payment_methods WHERE number_card = p_payment_card) THEN
        -- If it exists, update the money_card field
        UPDATE payment_methods
        SET money_card = money_card + 1000
        WHERE number_card = p_payment_card;
    ELSE
        -- If it doesn't exist, insert a new record
        INSERT INTO payment_methods (number_card, money_card)
        VALUES (p_payment_card, 1000);
    END IF;
END;
$$;
 Y   DROP PROCEDURE public.add_or_update_payment_method(IN p_payment_card character varying);
       public          postgres    false            �            1255    33135    delete_info_on_client_delete()    FUNCTION     b  CREATE FUNCTION public.delete_info_on_client_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Видаляємо записи з таблиці info, де nubercar_id відповідає numbercar_client видаленого клієнта
    DELETE FROM info
    WHERE nubercar_id = OLD.numbercar_client;

    RETURN OLD;
END;
$$;
 5   DROP FUNCTION public.delete_info_on_client_delete();
       public          postgres    false            �            1255    33139    insert_update_payment_card()    FUNCTION     ^  CREATE FUNCTION public.insert_update_payment_card() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Перевіряємо, чи вже існує запис у payment_methods з таким номером картки
    IF NOT EXISTS (SELECT 1 FROM payment_methods WHERE number_card = NEW.payment_card) THEN
        -- Якщо запису немає, додаємо новий запис з балансом по замовчуванню, наприклад 0
        INSERT INTO payment_methods (number_card, money_card) VALUES (NEW.payment_card, 0);
    END IF;
    RETURN NEW;
END;
$$;
 3   DROP FUNCTION public.insert_update_payment_card();
       public          postgres    false            �            1255    33177    issue_fine()    FUNCTION     t  CREATE FUNCTION public.issue_fine() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Вставляем штраф, используя id_client из telegram_info
    INSERT INTO fines (id_client, fine_amount, fine_date, paid)
    SELECT ti.id_client, 50.00, NOW(), FALSE
    FROM telegram_info ti
    WHERE ti.chat_id = NEW.chat_id;

    RETURN NEW;
END;
$$;
 #   DROP FUNCTION public.issue_fine();
       public          postgres    false            �            1255    33175    issue_fine_if_expired()    FUNCTION     (  CREATE FUNCTION public.issue_fine_if_expired() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.exit_date <= NOW() THEN
        INSERT INTO fines (id_client, fine_amount)
        VALUES (NEW.id_client, 50.00);  -- Set the fine amount as needed
    END IF;
    RETURN NEW;
END;
$$;
 .   DROP FUNCTION public.issue_fine_if_expired();
       public          postgres    false            �            1255    33173    issue_fines()    FUNCTION     �  CREATE FUNCTION public.issue_fines() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO fines (id_client, fine_amount)
    SELECT 
        c.id_client, 
        50.00  -- Set the fine amount
    FROM 
        clients c
    JOIN 
        info i ON c.numbercar_client = i.nubercar_id
    WHERE 
        i.exit_date < NOW() 
        AND NOT EXISTS (
            SELECT 1 
            FROM fines f 
            WHERE f.id_client = c.id_client 
            AND f.paid = FALSE
        );
END;
$$;
 $   DROP FUNCTION public.issue_fines();
       public          postgres    false            �            1255    24656    sync_info()    FUNCTION     w  CREATE FUNCTION public.sync_info() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Insert into info only if nubercar_id is not already present to avoid duplicates
    IF NOT EXISTS (SELECT 1 FROM info WHERE nubercar_id = NEW.numbercar_client) THEN
        INSERT INTO info (nubercar_id)
        VALUES (NEW.numbercar_client);
    END IF;
    RETURN NEW;
END;
$$;
 "   DROP FUNCTION public.sync_info();
       public          postgres    false            �            1255    33113    sync_parking_spaces()    FUNCTION     �  CREATE FUNCTION public.sync_parking_spaces() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Додати запис до parking_spaces при створенні нового клієнта
        INSERT INTO parking_spaces (place_number, floor, id_client)
        VALUES (1, 1, NEW.id_client); -- Значення 1 для place_number та floor як приклад
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Оновити запис у parking_spaces при оновленні клієнта
        UPDATE parking_spaces
        SET id_client = NEW.id_client
        WHERE id_client = OLD.id_client;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Видалити запис з parking_spaces при видаленні клієнта
        DELETE FROM parking_spaces
        WHERE id_client = OLD.id_client;
    END IF;
    RETURN NEW;
END;
$$;
 ,   DROP FUNCTION public.sync_parking_spaces();
       public          postgres    false            �            1255    24723    sync_payment_methods()    FUNCTION     T  CREATE FUNCTION public.sync_payment_methods() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if the number_card already exists
    IF EXISTS (SELECT 1 FROM payment_methods WHERE number_card = NEW.payment_card) THEN
        -- Update the money_card balance if it exists
        UPDATE payment_methods
        SET money_card = 1000
        WHERE number_card = NEW.payment_card;
    ELSE
        -- Insert a new record if it does not exist
        INSERT INTO payment_methods (number_card, money_card)
        VALUES (NEW.payment_card, 1000);
    END IF;
    RETURN NEW;
END;
$$;
 -   DROP FUNCTION public.sync_payment_methods();
       public          postgres    false            �            1259    24664    clients    TABLE     �   CREATE TABLE public.clients (
    id_client integer NOT NULL,
    name_client character varying(255),
    numbercar_client character varying(50),
    brand character varying(100),
    payment_card character varying(19)
);
    DROP TABLE public.clients;
       public         heap    postgres    false            �            1259    24663    clients_id_client_seq    SEQUENCE     �   CREATE SEQUENCE public.clients_id_client_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.clients_id_client_seq;
       public          postgres    false    216                       0    0    clients_id_client_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.clients_id_client_seq OWNED BY public.clients.id_client;
          public          postgres    false    215            �            1259    24672    info    TABLE       CREATE TABLE public.info (
    id_date date DEFAULT CURRENT_DATE NOT NULL,
    nubercar_id character varying(50),
    entry_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    exit_date timestamp without time zone DEFAULT (CURRENT_TIMESTAMP + '1 day'::interval)
);
    DROP TABLE public.info;
       public         heap    postgres    false            �            1259    33066    orders    TABLE       CREATE TABLE public.orders (
    id_order integer NOT NULL,
    id_service integer NOT NULL,
    order_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(50) DEFAULT 'pending'::character varying,
    id_client integer
);
    DROP TABLE public.orders;
       public         heap    postgres    false            �            1259    33065    orders_id_order_seq    SEQUENCE     �   CREATE SEQUENCE public.orders_id_order_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.orders_id_order_seq;
       public          postgres    false    223                       0    0    orders_id_order_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.orders_id_order_seq OWNED BY public.orders.id_order;
          public          postgres    false    222            �            1259    33117    parking_spaces    TABLE     �   CREATE TABLE public.parking_spaces (
    id integer NOT NULL,
    place_number integer,
    floor integer,
    id_client integer
);
 "   DROP TABLE public.parking_spaces;
       public         heap    postgres    false            �            1259    33116    parking_spaces_id_seq    SEQUENCE     �   CREATE SEQUENCE public.parking_spaces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.parking_spaces_id_seq;
       public          postgres    false    225                       0    0    parking_spaces_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.parking_spaces_id_seq OWNED BY public.parking_spaces.id;
          public          postgres    false    224            �            1259    24683    payment_methods    TABLE     �   CREATE TABLE public.payment_methods (
    id_card integer NOT NULL,
    number_card character varying(255),
    money_card numeric DEFAULT 1000
);
 #   DROP TABLE public.payment_methods;
       public         heap    postgres    false            �            1259    24682    payment_methods_id_card_seq    SEQUENCE     �   CREATE SEQUENCE public.payment_methods_id_card_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.payment_methods_id_card_seq;
       public          postgres    false    219                       0    0    payment_methods_id_card_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.payment_methods_id_card_seq OWNED BY public.payment_methods.id_card;
          public          postgres    false    218            �            1259    32913    service    TABLE     �   CREATE TABLE public.service (
    id_service integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    price numeric(10,2) NOT NULL,
    active boolean DEFAULT true
);
    DROP TABLE public.service;
       public         heap    postgres    false            �            1259    32912    service_id_service_seq    SEQUENCE     �   CREATE SEQUENCE public.service_id_service_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.service_id_service_seq;
       public          postgres    false    221                       0    0    service_id_service_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.service_id_service_seq OWNED BY public.service.id_service;
          public          postgres    false    220            �            1259    33141    telegram_info    TABLE     c   CREATE TABLE public.telegram_info (
    chat_id bigint NOT NULL,
    id_client integer NOT NULL
);
 !   DROP TABLE public.telegram_info;
       public         heap    postgres    false            ?           2604    24667    clients id_client    DEFAULT     v   ALTER TABLE ONLY public.clients ALTER COLUMN id_client SET DEFAULT nextval('public.clients_id_client_seq'::regclass);
 @   ALTER TABLE public.clients ALTER COLUMN id_client DROP DEFAULT;
       public          postgres    false    215    216    216            G           2604    33069    orders id_order    DEFAULT     r   ALTER TABLE ONLY public.orders ALTER COLUMN id_order SET DEFAULT nextval('public.orders_id_order_seq'::regclass);
 >   ALTER TABLE public.orders ALTER COLUMN id_order DROP DEFAULT;
       public          postgres    false    223    222    223            J           2604    33120    parking_spaces id    DEFAULT     v   ALTER TABLE ONLY public.parking_spaces ALTER COLUMN id SET DEFAULT nextval('public.parking_spaces_id_seq'::regclass);
 @   ALTER TABLE public.parking_spaces ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    225    224    225            C           2604    24686    payment_methods id_card    DEFAULT     �   ALTER TABLE ONLY public.payment_methods ALTER COLUMN id_card SET DEFAULT nextval('public.payment_methods_id_card_seq'::regclass);
 F   ALTER TABLE public.payment_methods ALTER COLUMN id_card DROP DEFAULT;
       public          postgres    false    218    219    219            E           2604    32916    service id_service    DEFAULT     x   ALTER TABLE ONLY public.service ALTER COLUMN id_service SET DEFAULT nextval('public.service_id_service_seq'::regclass);
 A   ALTER TABLE public.service ALTER COLUMN id_service DROP DEFAULT;
       public          postgres    false    221    220    221            �          0    24664    clients 
   TABLE DATA           `   COPY public.clients (id_client, name_client, numbercar_client, brand, payment_card) FROM stdin;
    public          postgres    false    216   ga       �          0    24672    info 
   TABLE DATA           K   COPY public.info (id_date, nubercar_id, entry_date, exit_date) FROM stdin;
    public          postgres    false    217   Lc                 0    33066    orders 
   TABLE DATA           U   COPY public.orders (id_order, id_service, order_date, status, id_client) FROM stdin;
    public          postgres    false    223   d                 0    33117    parking_spaces 
   TABLE DATA           L   COPY public.parking_spaces (id, place_number, floor, id_client) FROM stdin;
    public          postgres    false    225   �d       �          0    24683    payment_methods 
   TABLE DATA           K   COPY public.payment_methods (id_card, number_card, money_card) FROM stdin;
    public          postgres    false    219   e                  0    32913    service 
   TABLE DATA           O   COPY public.service (id_service, name, description, price, active) FROM stdin;
    public          postgres    false    221   �e                 0    33141    telegram_info 
   TABLE DATA           ;   COPY public.telegram_info (chat_id, id_client) FROM stdin;
    public          postgres    false    226   *g                  0    0    clients_id_client_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.clients_id_client_seq', 143, true);
          public          postgres    false    215                       0    0    orders_id_order_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.orders_id_order_seq', 58, true);
          public          postgres    false    222                       0    0    parking_spaces_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.parking_spaces_id_seq', 43, true);
          public          postgres    false    224                       0    0    payment_methods_id_card_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.payment_methods_id_card_seq', 2420, true);
          public          postgres    false    218                       0    0    service_id_service_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.service_id_service_seq', 7, true);
          public          postgres    false    220            L           2606    33100    clients clients_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id_client);
 >   ALTER TABLE ONLY public.clients DROP CONSTRAINT clients_pkey;
       public            postgres    false    216            Z           2606    33073    orders orders_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id_order);
 <   ALTER TABLE ONLY public.orders DROP CONSTRAINT orders_pkey;
       public            postgres    false    223            \           2606    33122 "   parking_spaces parking_spaces_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.parking_spaces
    ADD CONSTRAINT parking_spaces_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.parking_spaces DROP CONSTRAINT parking_spaces_pkey;
       public            postgres    false    225            T           2606    33191 $   payment_methods payment_methods_pkey 
   CONSTRAINT     g   ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT payment_methods_pkey PRIMARY KEY (id_card);
 N   ALTER TABLE ONLY public.payment_methods DROP CONSTRAINT payment_methods_pkey;
       public            postgres    false    219            X           2606    32921    service service_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.service
    ADD CONSTRAINT service_pkey PRIMARY KEY (id_service);
 >   ALTER TABLE ONLY public.service DROP CONSTRAINT service_pkey;
       public            postgres    false    221            ^           2606    33145     telegram_info telegram_info_pkey 
   CONSTRAINT     c   ALTER TABLE ONLY public.telegram_info
    ADD CONSTRAINT telegram_info_pkey PRIMARY KEY (chat_id);
 J   ALTER TABLE ONLY public.telegram_info DROP CONSTRAINT telegram_info_pkey;
       public            postgres    false    226            N           2606    33022    clients unique_name 
   CONSTRAINT     U   ALTER TABLE ONLY public.clients
    ADD CONSTRAINT unique_name UNIQUE (name_client);
 =   ALTER TABLE ONLY public.clients DROP CONSTRAINT unique_name;
       public            postgres    false    216            R           2606    32895    info unique_nubercar_id 
   CONSTRAINT     Y   ALTER TABLE ONLY public.info
    ADD CONSTRAINT unique_nubercar_id UNIQUE (nubercar_id);
 A   ALTER TABLE ONLY public.info DROP CONSTRAINT unique_nubercar_id;
       public            postgres    false    217            V           2606    32898 "   payment_methods unique_number_card 
   CONSTRAINT     d   ALTER TABLE ONLY public.payment_methods
    ADD CONSTRAINT unique_number_card UNIQUE (number_card);
 L   ALTER TABLE ONLY public.payment_methods DROP CONSTRAINT unique_number_card;
       public            postgres    false    219            P           2606    32893    clients unique_numbercar_client 
   CONSTRAINT     f   ALTER TABLE ONLY public.clients
    ADD CONSTRAINT unique_numbercar_client UNIQUE (numbercar_client);
 I   ALTER TABLE ONLY public.clients DROP CONSTRAINT unique_numbercar_client;
       public            postgres    false    216            i           2620    33176    info check_exit_date    TRIGGER     y   CREATE TRIGGER check_exit_date AFTER UPDATE ON public.info FOR EACH ROW EXECUTE FUNCTION public.issue_fine_if_expired();
 -   DROP TRIGGER check_exit_date ON public.info;
       public          postgres    false    244    217            j           2620    33179 !   telegram_info insert_fine_trigger    TRIGGER     {   CREATE TRIGGER insert_fine_trigger AFTER INSERT ON public.telegram_info FOR EACH ROW EXECUTE FUNCTION public.issue_fine();
 :   DROP TRIGGER insert_fine_trigger ON public.telegram_info;
       public          postgres    false    246    226            c           2620    33129 #   clients sync_parking_spaces_trigger    TRIGGER     �   CREATE TRIGGER sync_parking_spaces_trigger AFTER INSERT OR DELETE OR UPDATE ON public.clients FOR EACH ROW EXECUTE FUNCTION public.sync_parking_spaces();
 <   DROP TRIGGER sync_parking_spaces_trigger ON public.clients;
       public          postgres    false    241    216            d           2620    33098 $   clients sync_payment_methods_trigger    TRIGGER     �   CREATE TRIGGER sync_payment_methods_trigger AFTER INSERT ON public.clients FOR EACH ROW EXECUTE FUNCTION public.sync_payment_methods();
 =   DROP TRIGGER sync_payment_methods_trigger ON public.clients;
       public          postgres    false    228    216            e           2620    33137 ,   clients trigger_delete_info_on_client_delete    TRIGGER     �   CREATE TRIGGER trigger_delete_info_on_client_delete AFTER DELETE ON public.clients FOR EACH ROW EXECUTE FUNCTION public.delete_info_on_client_delete();
 E   DROP TRIGGER trigger_delete_info_on_client_delete ON public.clients;
       public          postgres    false    229    216            f           2620    24681    clients trigger_sync_info    TRIGGER     �   CREATE TRIGGER trigger_sync_info AFTER INSERT OR UPDATE OF numbercar_client ON public.clients FOR EACH ROW EXECUTE FUNCTION public.sync_info();
 2   DROP TRIGGER trigger_sync_info ON public.clients;
       public          postgres    false    227    216    216            g           2620    24724 $   clients trigger_sync_payment_methods    TRIGGER     �   CREATE TRIGGER trigger_sync_payment_methods AFTER INSERT OR UPDATE OF payment_card ON public.clients FOR EACH ROW EXECUTE FUNCTION public.sync_payment_methods();
 =   DROP TRIGGER trigger_sync_payment_methods ON public.clients;
       public          postgres    false    216    228    216            h           2620    33140 #   clients trigger_update_payment_card    TRIGGER     �   CREATE TRIGGER trigger_update_payment_card AFTER INSERT OR UPDATE ON public.clients FOR EACH ROW EXECUTE FUNCTION public.insert_update_payment_card();
 <   DROP TRIGGER trigger_update_payment_card ON public.clients;
       public          postgres    false    216    243            _           2606    33185    orders fk_orders_clients    FK CONSTRAINT     �   ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_orders_clients FOREIGN KEY (id_client) REFERENCES public.clients(id_client) ON DELETE CASCADE;
 B   ALTER TABLE ONLY public.orders DROP CONSTRAINT fk_orders_clients;
       public          postgres    false    223    4684    216            `           2606    33079    orders orders_id_service_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_id_service_fkey FOREIGN KEY (id_service) REFERENCES public.service(id_service);
 G   ALTER TABLE ONLY public.orders DROP CONSTRAINT orders_id_service_fkey;
       public          postgres    false    4696    223    221            a           2606    33123 ,   parking_spaces parking_spaces_id_client_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.parking_spaces
    ADD CONSTRAINT parking_spaces_id_client_fkey FOREIGN KEY (id_client) REFERENCES public.clients(id_client) ON DELETE CASCADE;
 V   ALTER TABLE ONLY public.parking_spaces DROP CONSTRAINT parking_spaces_id_client_fkey;
       public          postgres    false    216    4684    225            b           2606    33154 *   telegram_info telegram_info_id_client_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.telegram_info
    ADD CONSTRAINT telegram_info_id_client_fkey FOREIGN KEY (id_client) REFERENCES public.clients(id_client) ON DELETE CASCADE;
 T   ALTER TABLE ONLY public.telegram_info DROP CONSTRAINT telegram_info_id_client_fkey;
       public          postgres    false    216    226    4684            �   �  x�]RMo�@=?�
��k'>��q�	���E,�b�P���"��"T�J�zQ"����0���Y�V�jm��7oތ����%����z��5-���Җ�h6=?P�6����F�F\��/P��4�S}��\:��Q�ʍVKP��r<�a���qOq�V����t�-�NI�?��l053�\��{��3�>U�i�ߣ�d7Ak�),z��:�~Ѫj֥���#S��\�C�`8�Ů1�q�)|ͤ߻��D0�{���bXL`�=�Ǡt�޷U�bdZ�^OPiO�W/'o�����x���1gU9�b+?�,��q����gx4�L�1,~��#��Y�����w��5��ĸ�����G��+���dm�*3_����lg'�;x��(�%�B ^$��O��`�2��$�}����A�"+�׼�Jy~h�������V�%N�~����蒯K��������y��q�?��\�      �   �   x��λ� ���L��!6���#!C�N���#E��Ъҝ��wB��U���6��౻�Vc�q������8o�q$�N3י&b�y�:�LL��\gY�qk�:�J�����H�J��D��ur&˝�B��?����?����v�PpA)	�;��X�*m����}���@v��Ν�I<����         z   x�]�1�@D��>E.��=�w�>DN�����WDB�4�ӟ��	_%V�"R��I����������:�"��������w�$�b8]�k/��<�<d����q~�q�����/�&)�         V   x�%˹�0�(�c
��^����=	FH�!Aզk�N�#���@F�AM�k&�Ы��n��t��t��ʸх�~-~�U��      �   m   x�]б�0��&�d9�w��~������ *� x�a�y���\|�d�0�H9DfQ��*
��h@Ċv�xQB�M�Dт�xɯo�޸+��@����[7�S~���-N<#          �  x��S[N�@�V10�O݌�p�Z�&M�i�&� )��R�¹;���Ц�����3]�TH�c�+��B,#!A��27x��h��������%��0�uh{Y�BV�x�^��t̃�3Xp��w����	�o�Æ�o��\B^썑��B��l��,��/��Zl,+s�ȞK��FJ�GAρ��ö���J�@%��i�>�e��z�UhU@��9J~f��3./5c��u8vd��͈
5=��2u��EE;A��I3S��j�Zm"���7�V��`���Z'�zv�F7:�0��O^GѶ�:=���r����y�G�z�m�	!��i7ȝzqIg��J��ɕ]YO@��>ٗ|\��u��	�������)�*�8�`��� �I眞D���V.��aE<m��?�j�{��o�Ҁy            x�322474654�441����� #
      