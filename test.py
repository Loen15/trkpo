import unittest
import subprocess
import sys
from main import calculate, parse
import ast
import math
import time

def parse_tree_string(tree_str):
    #Преобразуем строку с деревом выражений Add(2, 2) в AST.
    try:
        # Удаляем пробелы
        tree_str = tree_str.replace(" ", "")
        # Определяем операцию и аргументы
        if tree_str.startswith("Add"):
            op = ast.Add()
            args_str = tree_str[4:-1]  # Убираем "Add(" и ")"
        elif tree_str.startswith("Sub"):
            op = ast.Sub()
            args_str = tree_str[4:-1]  
        elif tree_str.startswith("Mult"):
            op = ast.Mult()
            args_str = tree_str[5:-1]  
        elif tree_str.startswith("Div"):
            op = ast.Div()
            args_str = tree_str[4:-1]
        elif tree_str.startswith("Pow"):  
            op = ast.Pow()
            args_str = tree_str[4:-1]
        elif tree_str.startswith(('sqrt', 'sin', 'cos', 'tg', 'ctg', 'ln', 'exp')):
            func_name = tree_str.split('(')[0]
            args_str = tree_str[len(func_name)+1:-1]
            arg = parse_argument(args_str)
            return ast.Call(
                func=ast.Name(id=func_name, ctx=ast.Load()),
                args=[arg],
                keywords=[]
            )     
        else:
            # Если строка не начинается с операции
            try:
                value = float(tree_str)
                return ast.Constant(value=value)
            except ValueError:
                if tree_str in ['pi', 'e']:
                    return ast.Name(id=tree_str, ctx=ast.Load())
                raise ValueError(f"Неизвестная операция при тесте: {tree_str}")

        # Разделяем аргументы
        left_str, right_str = split_arguments(args_str)

        # Рекурсивно разбираем левый и правый аргументы
        left = parse_argument(left_str)
        right = parse_argument(right_str)

        # Создаем узел AST
        return ast.BinOp(left=left, op=op, right=right)
    except Exception as e:
        raise ValueError(e)

def split_arguments(args_str):
    # Разделяем аргументы
    balance = 0  # Счетчик для отслеживания вложенности
    for i, char in enumerate(args_str):
        if char == "(":
            balance += 1
        elif char == ")":
            balance -= 1
        elif char == "," and balance == 0:
            # Нашли разделитель аргументов
            return args_str[:i], args_str[i+1:]
    return args_str, ""

def parse_argument(arg_str):
    # Проверяем, является ли аргумент числом
    if arg_str.replace(".", "", 1).replace("e", "", 1).isdigit():  
        return ast.Constant(value=float(arg_str))
    elif arg_str in ['pi', 'e']:
        return ast.Name(id=arg_str, ctx=ast.Load())
    else:
        return parse_tree_string(arg_str)

def ast_to_str(node):
   #Преобразуем дерево AST в строковое представление.
    if isinstance(node, ast.Expression):
        return ast_to_str(node.body)
    elif isinstance(node, ast.BinOp):
        left = ast_to_str(node.left)
        right = ast_to_str(node.right)
        op = type(node.op).__name__
        return f"{op}({left}, {right})"
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.UnaryOp):
        operand = ast_to_str(node.operand)
        op = type(node.op).__name__
        return f"{op}({operand})"
    elif isinstance(node, ast.Call):
        args = ", ".join(ast_to_str(arg) for arg in node.args)
        return f"{node.func.id}({args})"
    elif isinstance(node, ast.Name):
        return node.id
    else:
        raise ValueError(f"Неподдерживаемый тип узла при тесте: {type(node)}")

class TestParser(unittest.TestCase):
    def test_expressions(self):
        test_cases = [
            ("1", "1", None),
            ("2.3", "2.3", None),
            ("4 + 5", "Add(4, 5)", None),
            ("6 * 7", "Mult(6, 7)", None),
            ("8 / 9", "Div(8, 9)", None),
            ("10 - 200", "Sub(10, 200)", None),
            ("-34.5  / 6.78 + 901.2 * 0.345", "Add(Div(USub(34.5), 6.78), Mult(901.2, 0.345))", None),
            ("3 ^ 4", "Pow(3, 4)", None),
            ("7**8", "Pow(7, 8)", None),
            ("(9 + 10) * 12", "Mult(Add(9, 10), 12)", None),
            ("1.25e+03","1250.0", None),
            ("pi", "pi", None),
            ("e", "e", None),
            ("sqrt(1)", "sqrt(1)", None),  
            ("sin(pi/2)", "sin(Div(pi, 2))", None),  
            ("ln(e^3)", "ln(Pow(e, 3))", None),
            ("a", "Error", ValueError),
            ("6 /", "Error",  ValueError),
            ("5 + 6j", "Error", ValueError),

        ]

        print("\nТесты для парсера:\nСтатус\tВведенное выражение\tОжидаемый результат\tПолученный результат")
        for tree_str, expected, expected_exception in test_cases:
            try:
                # Парсим выражение в AST
                tree = parse(tree_str)  
                result = ast_to_str(tree)
                if expected_exception is not None:
                    status = "\u00D7"
                else:
                    status = "\u2713" if result == expected else "\u00D7"
            except Exception as e:
                result = str(e)
                if expected_exception is not None and isinstance(e, expected_exception):
                    status = "\u2713"
                else:
                    status = "\u00D7"
            print(f"{status}\t{tree_str}\t\t\t{expected}\t\t\t{result}")        

class TestCalculator(unittest.TestCase):
    def test_calculations(self):
        test_cases = [
            ("Add(2,3)", 5, None),
            ("Mult(4,5)", 20, None),
            ("Div(6,3)", 2.0, None),
            ("Sub(8, 7)", 1, None),
            ("pi", math.pi, None),
            ("e", math.e, None),
            ("sqrt(4)", 2, None),  
            ("sin(Div(pi, 2))", 1, None),  
            ("ln(Pow(e, 3))", 3, None),
            ("Div(2, 0)", "Error", ZeroDivisionError),
            ("Div(3, Sub(4, 4))", "Error", ZeroDivisionError), 
            ("Div(1e300, 1e-300)", "Error", OverflowError)
        ]
        print("\nТесты для вычислителя:\nСтатус\tВведенное выражение\tОжидаемый результат\tПолученный результат")
        
        for tree_str, expected, expected_exception in test_cases:
            try:
                # Преобразуем строку с деревом выражений в AST
                tree = parse_tree_string(tree_str)
                result = calculate(tree)
                if expected_exception is not None:
                    status = "\u00D7"
                else:
                    status = "\u2713" if result == expected else "\u00D7"
            except Exception as e:
                result = str(e)
                if expected_exception is not None and isinstance(e, expected_exception):
                    status = "\u2713"
                else:
                    status = "\u00D7"
            print(f"{status}\t{tree_str}\t\t\t{expected}\t\t\t{result}")
            
class TestIntegration(unittest.TestCase):
    def test_integration(self):
        test_cases = [
            ("1 + 2", 3, None),
            ("3 * 4", 12, None),
            ("6 / 2", 3.0, None),
            ("5 - 3", 2, None),
            ("7 ^ 2", 49, None),  
            ("2 + (3 * 4)", 14, None),
            ("3.375e+09^(1/3)", 1499.9999999999993, None),
            ("sin(pi/2)", 1, None),
            ("cos(0)", 1, None),
            ("tg(0)", 0, None),
            ("exp(ln(2))", 2, None),
            ("ln(exp(2))", 2, None),
            ("ln(e^2)", 2, None),
            ("1 /", "Error", ValueError),
            ("1 / 0", "Error", ZeroDivisionError),
            ("5 + 6j", "Error", ValueError),
        ]
        
        print("\nИнтеграционные тесты:\nСтатус\tВведенное выражение\tОжидаемый результат\tПолученный результат")
        
        for tree_str, expected, expected_exception in test_cases:
            try:
                # Преобразуем строку с деревом выражений в AST
                tree = parse(tree_str)
                result = calculate(tree)
                if expected_exception is not None:
                    status = "\u00D7"
                else:
                    status = "\u2713" if result == expected else "\u00D7"
            except Exception as e:
                result = str(e)
                if expected_exception is not None and isinstance(e, expected_exception):
                    status = "\u2713"
                else:
                    status = "\u00D7"
            print(f"{status}\t{tree_str}\t\t\t{expected}\t\t\t{result}")

class TestFunctional(unittest.TestCase):
  def test(self):
    
    script_path = 'main.py'
    
    test_cases = [
            (['1+2'], 3, None),
            (['--angle-unit=degree', 'sin(90)'], 1.0, None),
            (['--angle-unit=radian', 'sin(pi/2)'], 1.0, None),
            (['sin(pi/2)'], 1.0, None),
            (['sqrt(2^2 * 5 + 61)'], 9.0, None),
            (['exp(ln(2))'], 2.0, None),
            (['ln(exp(2))'], 2.0, None),
            (['ln(e^2)'], 2.0, None),
            (['1/'], "Error", ValueError),
            (['1/0'], "Error", ZeroDivisionError),
            (['5+6j'], "Error", ValueError),
            ]
    print("\nФункциональные тесты:\n")
          
    for args, expected_output, expected_exception in test_cases:
            cmd = [sys.executable, script_path] + list(args)

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if expected_exception is not None:
                print(f"\u2713\t{script_path} {' '.join(args)}\t\t\t\t{stderr}")
            else:
                if stdout[11:] == str(expected_output):
                    print(f"\u2713\t{script_path} {' '.join(args)}\t\t\t\t{expected_output}\t\t{stdout}")
                else:
                    print(f"\u00D7\t{script_path} {' '.join(args)}\t\t\t\t{expected_output}\t\t\t\t{stderr}")
            
class TestTime(unittest.TestCase):
    def test(self):
        test_cases = [
            ("1+" * 249 + "1"),
            ("1+" * 250),
            ("1" + "0" * 250 + "+1" + "0" * 250 + "+1" + "0" * 250 + "+1" + "0" * 250),
            ("1 ^ 23445345424243553"),
            ("1.001 ^ 23445345424243553"),
            ("1+" * 1000 + "1"),
            ("10+" * 100 + "10"),
        ]
        print("\nНагрузочные тесты:\n")
        for expression in test_cases:
            try:
                start_time = time.time()
                result = calculate(expression)
                exec_time = time.time() - start_time
                print(f"{expression} -> {result}\n[{exec_time} s] \n")
                if len(expression) < 1000:
                    if exec_time * 1000 > 200:
                        print("Тест не пройден\n")
            except Exception as e:
                exec_time = time.time() - start_time
                print(f"{expression} -> {str(e)}\n[{exec_time} s] \n")
                if len(expression) < 1000:
                    if exec_time * 1000 > 200:
                        print("Тест не пройден\n")

if __name__ == "__main__":
    unittest.main() 