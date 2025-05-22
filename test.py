import unittest
from main import calculate, parse
import ast

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
        else:
            # Если строка не начинается с операции
            try:
                value = float(tree_str)
                return ast.Constant(value=value)
            except ValueError:
                raise ValueError(f"Неизвестная операция: {tree_str}")

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
    raise ValueError(f"Не удалось разделить аргументы: {args_str}")

def parse_argument(arg_str):
    # Проверяем, является ли аргумент числом
    if arg_str.replace(".", "", 1).replace("e", "", 1).isdigit():  
        return ast.Constant(value=float(arg_str))
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
    else:
        raise ValueError(f"Неподдерживаемый тип узла: {type(node)}")

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
            ("a", "Error", ValueError),
            ("6 /", "Error",  ValueError),
            ("7**8", "Error", ValueError),
            ("(9 + 10) * 12", "Error", ValueError),
            ("3 ^ 4", "Error", ValueError),
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
            ("Div(2, 0)", "Error", ZeroDivisionError),
            ("Div(3, Sub(4, 4))", "Error", ZeroDivisionError), 
            ("Div(1e300, 1e-300)", "Error", OverflowError)
        ]
        print("\nТесты для вычислителя:")
        
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

if __name__ == "__main__":
    unittest.main() 