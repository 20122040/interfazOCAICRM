CREATE TABLE [account] (
  username TEXT PRIMARY KEY NOT NULL,
  password TEXT
);

CREATE TABLE [procesos] (
  groupId TEXT PRIMARY KEY NOT NULL,
  nombreProceso TEXT NOT NULL UNIQUE,
  estado NUMERIC NOT NULL DEFAULT 1,
  link TEXT,
  pago NUMERIC,
  moneda TEXT DEFAULT "Soles"
);

CREATE TABLE [ultima_act](
  id NUMERIC PRIMARY KEY NOT NULL,
  stamp TEXT
);

CREATE TABLE [ultima_val](
  id NUMERIC PRIMARY KEY NOT NULL,
  stamp TEXT
);

INSERT INTO procesos ("nombreProceso","groupId","estado","pago","moneda","link") values
("MBA GI ICA IX 2018","30000000283987",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00410"),
("MBA GI CUSCO XXIII 2018","30000000499230",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00411"),
("MBA CHICLAYO XVII 2018","30000000831910",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00413"),
("MAESTRIA CORPORATIVA INTERNACIONAL EN DIRECCIÓN DE MARKETING 2018-1 IX","30000000581549",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00412"),
("MBA G INT LIMA 2018-2 INTENSIVO CXXIX","30000000792386",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00425"),
("DBA SEMIPRESENCIAL II 2018","30000000524828",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00429"),
("Maestría Corporativa Internacional en Dirección de Marketing I 2018 - 1","30000000422764",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00430"),
("Maestría Corporativa Internacional en Tecnologías de la Información I 2018 - 1","30000000675755",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00431"),
("Maestría Corporativa Internacional en Negocios Jurídicos I 2018 - 1","30000000928863",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00432"),
("Maestría Corporativa Internacional en Emprendimiento I 2018 - 1","30000000130507",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00433"),
("Maestría Corporativa Internacional en Gestión del Talento I 2018 - 1","30000000276674",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00434"),
("MBA GI Trujillo XXII","30000000185394",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00445"),
("MBA GI ONLINE XXXIII 2018","30000000346240",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00440"),
("MBA GI Online XXXII Corporativo - 2018","30000000916663",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00439"),
("Tricontinental MBA V 2018","30000000796115",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00448"),
("MBA G INT LIMA 2018-2 DOMINICAL CXXX","30000000548806",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00449"),
("MBA G INT LIMA 2018-2 QUINCENAL CXXXI","30000000657114",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00450"),
("MBA G INT LIMA 2018-2 EJECUTIVO CXXXII","30000000328070",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00451"),
("MBA G LIMA SAN MIGUEL 2018-1 I ","30000000891493",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00452"),
("MBA GI CUSCO XXIII 2018-2","30000000136489",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00447"),
("MAESTRIA CORPORATIVA INTERNACIONAL EN FINANZAS 2018-2 XI","30000000185977",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00465"),
("MAESTRIA CORPORATIVA INTERNACIONAL EN SUPPLY CHAIN MANAGEMENT 2018-2","30000000133155",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00466"),
("MBA G INT LIMA 2018-3 INTENSIVO CXXXIII","30000000586906",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00473"),
("MBA GI CUSCO XXIV 2018","30000000332490",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00475"),
("MBA GI PIURA XXI 2018-2","30000000796733",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00476"),
("MBA G INT LIMA 2018-3 QUINCENAL CXXXIV","30000000626385",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00482"),
("MBA G INT LIMA 2018-3 DOMINICAL CXXXV","30000000670797",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00480"),
("MBA G INT LIMA 2018-3 SAN ISIDRO CXXXVI","30000000339681",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00481"),
("MBA GI HUANCAYO XIV","30000000757316",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00478"),
("MBA GI CAJAMARCA XIII","30000000927817",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00479"),
("MBA GI ONLINE XXXIV 2018","30000000698434",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00477"),
("MBA GI Arequipa XXVII","30000000787823",1,500,"Soles","http://campusvirtual.pucp.edu.pe/pucp/oca/oawadmin/oawadmin?accion=IniciarInscripcion&codProceso=00446"),
("MBA G INT LIMA 2017-3 EJECUTIVO CXXIV","300000021596525",0,650.0,"Soles",""),
("MBA EN GESTIÓN DE SALUD I 2017","300000021102293",0,650.0,"Soles",""),
("MBA G INT LIMA 2017-3 DOMINICAL CXXII","300000021596474",0,650.0,"Soles",""),
("MBA G INT LIMA IH 2018-1 CORPORATIVO","300000022788181",0,650.0,"Soles",""),
("GLOBAL MBA XI 2017","300000019676566",0,650.0,"Soles",""),
("MAESTRIA SUPPLY CHAIN MANAGEMENT 2017-2","300000021246744",0,650.0,"Soles",""),
("MBA G INT LIMA 2017-3 INTENSIVO CXXI","300000021596533",0,650.0,"Soles",""),
("MAESTRIA CORPORATIVA INTERNACIONAL EN FINANZAS CORPORATIVAS IX 2017-2","300000021246724",0,650.0,"Soles",""),
("PROCESO EJEMPLO","300000017127709",0,230.0,"Soles","http://pucp.edu.pe");

INSERT INTO ultima_act values (1,'-');

INSERT INTO ultima_val values (1,'-');