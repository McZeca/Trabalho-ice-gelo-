#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors
    student1 number/name: Francisco Almeida 67882
        student1 contribution (%): 50
        contribution description: Os colegas ajudaram-se mutuamente
            
    student2 number/name: Tomás Reis 67198
        student2 contribution (%): 50
        contribution description: Os colegas ajudaram-se mutuamente

"""

# %%
# MODULES
#
import sqlite3
import math
import matplotlib.pyplot as plt

# %%
# CREATE TABLES
#
def cmd_create_tables(conn: sqlite3.Connection) -> None:
    """
    Cria duas tabelas vazias na base de dados. Caso já existam tabelas na 
    base de dados, a função apaga-as.

    A função cria as seguintes tabelas:
    - Tests: Armazena informações sobre os testes realizados, com os campos:
        .id
        .mat_id
        .year.
        .temp_ini
        .certification
    - Samples: Armazena informações sobre as amostras coletadas, com os campos:
        .id
        .test_id
        .time
        .temperature
    """
    drop_tests = "DROP TABLE IF EXISTS Tests"
    drop_samples = "DROP TABLE IF EXISTS Samples"
    
    create_tests = """CREATE TABLE Tests (
                    id INTEGER PRIMARY KEY,
                    mat_id TEXT,
                    year INTEGER, 
                    temp_ini REAL,
                    certification TEXT);"""
    create_samples = """CREATE TABLE Samples (
                    id INTEGER PRIMARY KEY, 
                    test_id INTEGER, 
                    time INTEGER,
                    temperature REAL);"""
    
    try:
        conn.execute(drop_tests)
        conn.execute(drop_samples)
        conn.execute(create_tests)
        conn.execute(create_samples)
        
    except sqlite3.Error:
        print('Erro ao criar tabelas.')

    pass


# %%
# LOAD ONE TEST
#
def cmd_load_test(conn: sqlite3.Connection, args: str) -> None:
    """
    Carrega os dados dos ficheiros de input nas tabelas "Tests" e "Samples".
    """
    files = args.split(';')

    cmd1 = 'INSERT INTO Tests VALUES (?, ?, ?, ?, ?);'
    cmd2 = 'INSERT INTO Samples VALUES (?, ?, ?, ?);'

    for file in files:

        file = open(file, 'r')
        lines = file.readlines()

        try:

            for line in lines[:5]:
                line.strip()
            values_Test = (int(lines[0].strip()), lines[2].strip(), int(lines[1].strip()), float(lines[4].strip()), lines[3].strip())
            conn.execute(cmd1, values_Test)

            for line in lines[5:]:
                elems = line.strip().split(';')
                values_Sample = (int(elems[0]), int(lines[0].strip()), int(elems[1]), float(elems[2]))
                conn.execute(cmd2, values_Sample)

        except sqlite3.IntegrityError: 
            pass
    
        file.close()
    conn.commit()

    pass



# %%
# WRITE A SUMMARY
#
def cmd_summary(conn: sqlite3.Connection, args: str) -> None:
    """
    Gera um resumo dos dados na base de dados.

    A função recupera o número total de registos nas tabelas "Tests" e "Samples"
    e retorna essa informação sobre a forma de strings na consola.
    O resumo considera condições especificadas nos argumentos (start, end e certification).
    """

    cmd1 = 'SELECT DISTINCT mat_id FROM Tests WHERE TRUE=TRUE'
    cmd2 = 'SELECT id FROM Tests WHERE mat_id=?'
    cmd3 = 'SELECT COUNT(*) FROM Samples WHERE test_id=?;'

    start, end, certif = args.split(';')
    
    conditions = []
    if start != "*":
        cmd1 += " AND year >= ?"
        cmd2 += " AND year >= ?"
        conditions.append(start)
    if end != "*":
        cmd1 += " AND year <= ?"
        cmd2 += " AND year <= ?"
        conditions.append(end)
    if certif != "*":
        cmd1 += " AND certification = ?"
        cmd2 += " AND certification = ?"
        conditions.append(certif)

    materials = conn.execute(cmd1, conditions).fetchall()
    print(str(len(materials)) + ' materials between ' + start + ' and ' + end + ' with certification ' + certif + ' :')  
    
    samples = 0
    conditions.insert(0, '')
    for material in materials:
        print('\t' + material[0])
        conditions[0] = material[0]
        all_ids = conn.execute(cmd2, conditions).fetchall()
        for id in all_ids:
            samples += conn.execute(cmd3, id).fetchall()[0][0]
    
    print('Total samples: ' + str(samples))

    pass


def cmd_summary_file(conn: sqlite3.Connection, args: str) -> None:
    """
    Escreve o mesmo resumo da função anterior num ficheiro de texto.
    """
    file_name, start, end, certif = args.split(';')

    file = open(file_name, 'w')

    cmd1 = 'SELECT mat_id FROM Tests WHERE TRUE=TRUE'
    cmd2 = 'SELECT id FROM Tests WHERE mat_id=?'
    cmd3 = 'SELECT COUNT(*) FROM Samples WHERE test_id=?;'
    
    conditions = []
    if start != "*":
        cmd1 += " AND year >= ?"
        cmd2 += " AND year >= ?"
        conditions.append(start)
    if end != "*":
        cmd1 += " AND year <= ?"
        cmd2 += " AND year <= ?"
        conditions.append(end)
    if certif != "*":
        cmd1 += " AND certification = ?"
        cmd2 += " AND certification = ?"
        conditions.append(certif)

    materials = conn.execute(cmd1, conditions).fetchall()
    file.write(str(len(materials)) + ' materials between ' + start + ' and ' + end + ' with certification ' + certif + ' :\n')
    
    samples = 0
    conditions.insert(0, '')
    for material in materials:
        file.write('\t' + material[0] + '\n')
        conditions[0] = material[0]
        all_ids = conn.execute(cmd2, conditions).fetchall()
        for id in all_ids:
            samples += conn.execute(cmd3, id).fetchall()[0][0]

    file.write('Total samples: ' + str(samples) + '\t')
    file.close()

    pass

# %%
# PLOT A GRAPH OF MATERIALS
#    
def cmd_plot(conn: sqlite3.Connection, args: str) -> None:
    """
    Gera um gráfico com os dados das amostras.

    A função recupera os dados das amostras da tabela "Samples" para determinados materiais, 
    expecificados nos argumentos da função, e gera um gráfico de dispersão da temperatura
    relativa em função do tempo. Ao mesmo tempo e no mesmo gráfico, a função calcula os
    valores previstos pelo modelo de Newton e traça a curva que descreve os dados segundo este modelo.
    """
    refs = args.split(';')

    cmd1 = "SELECT id, temp_ini FROM Tests WHERE mat_id = ?"
    cmd2 = "SELECT time, temperature FROM Samples WHERE test_id = ?"

    for ref in refs:
        tests = conn.execute(cmd1, (ref,)).fetchall()
        
        times = []
        temperatures_norm = []
        sum = 0
        num_points = 0
        for test_id, temp_ini in tests:
            samples = conn.execute(cmd2, (test_id,)).fetchall()
            num_points += len(samples)
            for sample in samples:
                times.append(sample[0])
                temperatures_norm.append(sample[1] / temp_ini)
                sum = sum + (-math.log(sample[1]/temp_ini) / sample[0])
        k = sum / num_points

        plt.scatter(times, temperatures_norm, marker='x')
        
        delta_t = max(times) / 1000
        newton_times = [0]
        for i in range(1000):
            newton_times.append(newton_times[i] + delta_t)

        newton_temperatures = []
        for time in newton_times:
            newton_temperatures.append(math.exp(-k * time))
            
        plt.plot(newton_times, newton_temperatures, label=ref)
    
    plt.title('Cooling over time')
    plt.xlabel('Elapsed time (hours)')
    plt.ylabel('Relative Temperature')
    plt.legend()
    plt.show()

    pass


# %%
# PLOT A GRAPH TO FILE
#


def cmd_plot_file(conn: sqlite3.Cursor, args: str) -> None:
    """
    Esta função efetua os mesmos processos da função anterior com a diferença que guarda 
    o gráfico num ficheiro ao invés de o mostrar na consola.
    """
    file_name = args.split(';')[0]
    refs = args.split(';')[1:]

    cmd1 = "SELECT id, temp_ini FROM Tests WHERE mat_id = ?"
    cmd2 = "SELECT time, temperature FROM Samples WHERE test_id = ?"

    for ref in refs:
        tests = conn.execute(cmd1, (ref,)).fetchall()
        
        times = []
        temperatures_norm = []
        sum = 0
        num_points = 0
        for test_id, temp_ini in tests:
            samples = conn.execute(cmd2, (test_id,)).fetchall()
            num_points += len(samples)
            for sample in samples:
                times.append(sample[0])
                temperatures_norm.append(sample[1] / temp_ini)
                sum = sum + (-math.log(sample[1]/temp_ini) / sample[0])
        k = sum / num_points

        plt.scatter(times, temperatures_norm, marker='x')
        
        delta_t = min(times) / 1000
        newton_times = [0]
        for i in range(1000):
            newton_times.append(newton_times[i] + delta_t)

        newton_temperatures = []
        for time in newton_times:
            newton_temperatures.append(math.exp(-k * time))
            
        plt.plot(newton_times, newton_temperatures, label=ref)
    
    plt.title('Cooling over time')
    plt.xlabel('Elapsed time (hours)')
    plt.ylabel('Relative Temperature')
    plt.legend()
    
    plt.savefig(file_name)
    plt.close()

    pass


# %%
# EXECUTE ONE COMMAND
#
def cmd_execute(conn: sqlite3.Connection, file_cmds: str) -> None:
    """
    Lê e executa uma série de comandos a partir de um ficheiro.

    A função abre o ficheiro especificado, lê cada linha como um comando, 
    e processa cada comando utilizando a função `process_one_cmd`.
    """
    file = open(file_cmds, 'r')
    lines = file.readlines()

    for line in lines:
            process_one_cmd(conn, upper_command(line.strip()))

    pass


# %%
# AUXILIAR FUNCTIONS
#

def strip_list(x: list[str]) -> list[str]:
    """
    Strip all the strings in the list
    """
    return [i.strip() for i in x]


def upper_command(s: str) -> str:
    """
    Converts the first word in 's' to uppercase.
    """
    words = strip_list(s.split(' ', maxsplit=1))
    words[0] = words[0].upper()
    cmd = ' '.join(words)
    return cmd


def read_command(f) -> str:
    """
    Reads a command.
    retuns the command word in uppercase followed by the given arguments.
    """
    if f is None:
        # reads from keyboard
        cmd = ''
        while cmd == '':
            cmd = input("Command: ").strip()
    else:
        # reads from file 'f'
        cmd = f.readline()
        #print(cmd)
        if cmd == '':
            cmd = 'QUIT'
    return upper_command(cmd.strip())


# %%
# PROCESS ONE COMMAND
#
def process_one_cmd(conn: sqlite3.Connection, comando: str) -> None:
    """
    Processa um comando individual e executa a função correspondente.

    Comandos suportados:
    - "CREATE_TABLES": Cria as tabelas na base de dados utilizando a função `cmd_create_tables`.
    - "LOAD_TEST": Carrega dados nas tabelas 'Tests' e "Samples" utilizando a função `cmd_load_test`.
    - "SUMMARY": Gera um resumo dos dados utilizando a função `cmd_summary`.
    - "SUMMARY_FILE": Escreve um resumo dos dados num ficheiro de texto utilizando a função `cmd_summary_file`.
    - "PLOT": Gera um gráfico com os dados das amostras utilizando a função `cmd_plot`.
    - "PLOT_FILE": Gera um gráfico com os dados das amostras e guarda-o num ficheiro utilizando a função `cmd_plot_file`.
    - "EXECUTE": Executa um comando utilizando a função `cmd_execute`.

    """
    comando = comando + ' '
    cmd = strip_list(comando.split(' ', 1))
    
    if cmd[0] == 'QUIT' or cmd[0] == '#':
        pass  # really nothing to do!
    elif cmd[0] == "CREATE_TABLES":
        cmd_create_tables(conn)
    elif cmd[0] == "LOAD_TEST":
        cmd_load_test(conn, cmd[1])
    elif cmd[0] == "SUMMARY":
        cmd_summary(conn, cmd[1])
    elif cmd[0] == "SUMMARY_FILE":
        cmd_summary_file(conn, cmd[1])
    elif cmd[0] == "PLOT":
        cmd_plot(conn, cmd[1])
    elif cmd[0] == "PLOT_FILE":
        cmd_plot_file(conn, cmd[1])
    elif cmd[0] == "EXECUTE":
        cmd_execute(conn, cmd[1])
    else:
        print('Unknown command!' + cmd[1])
    


# %%
# MAIN FUNTION TO PROCESS ALL COMMANDS
#

def process_cmds(db_file: str, inf=None) -> None:
    """
    Processes a sequence of commands, producing corresponding outputs.
    db_file: name of the database where to place/read the information.
    inf: (please ignore, call this function with only the first argument)
    """

    assert (db_file != "")

    #   open the database file
    conn = sqlite3.connect(db_file)

    # The main loop
    cmd = '#'
    while cmd != 'QUIT':
        if cmd[0] != '#':
            process_one_cmd(conn, cmd)
        cmd = read_command(inf)

    conn.commit()
    conn.close()
    print("BYE!")


def main():
    process_cmds("database.db")


if __name__ == '__main__':
    main()  # run program
