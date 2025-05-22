import sys
import ast
import operator as op
import argparse
import math
import re

# Парсер аргументов командной строки
parser = argparse.ArgumentParser(
    prog="python main.py",
    description="Вычисление выражений c поддержкой +, -, /, *, sin, cos, tg, ctg, sqrt, ln, exp, pi, e, аргументов тригонометрических функций в виде градусов и в виде радиан")
parser.add_argument("expression", nargs="?", help="Математическое выражение для вычисления типа '1+1'")
parser.add_argument("--angle-unit", choices=["degree", "radian"], default="radian",
                   help="Единицы измерения углов для тригонометрических функций. Значения: degree, radian (по умолчанию: radian)")  

operators = {
    ast.Add: op.add, # +
    ast.Sub: op.sub, # -
    ast.Mult: op.mul, # *
    ast.Div: op.truediv, # /
    ast.USub: op.neg, # унарный -
    ast.Pow: op.pow # возведение в степень  
}

functions = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tg': math.tan,
    'ctg': lambda x: 1/math.tan(x),
    'ln': math.log,
    'exp': math.exp,
}

constants = {
    'pi': math.pi,
    'e': math.e,
}

def parse(expression):
    try:
        # Запрещаем пробелы между цифрами, в том числе вида 1e 10
        if re.search(r"\d\s+\d", expression) or re.search(r"e\s+\d", expression) or re.search(r"\d\s+e", expression):
            raise ValueError("Пробел между цифрами не допускается.")
        
        # Удаляем лишние пробелы
        expression = " ".join(expression.split())
        
         # Проверяем на наличие недопустимых символов
        for token in re.findall(r'[a-zA-Z]+', expression):
            if token not in functions and token not in constants and not token.startswith(('sqrt', 'sin', 'cos', 'tg', 'ctg', 'ln', 'exp')):
                raise ValueError(f"Выражение содержит неразрешенные символы: {token}")
          
        # Заменяем ^ на ** для корректной работы
        expression = expression.replace('^', '**')
        
        # Преобразуем выражение в дерево AST
        tree = ast.parse(expression, mode='eval')
        return tree.body
    except (SyntaxError, TypeError, KeyError, ValueError) as e:
        raise ValueError(f"Ошибка парсера: Некорректное выражение: {e}")

def evaluate(node, angle_unit='radian'):
    #Рекурсивно обрабатываем AST-узлы
    if isinstance(node, ast.Constant): # числа 
        return node.value
    elif isinstance(node, ast.BinOp):  # бинарные операции
        left = evaluate(node.left, angle_unit)
        right = evaluate(node.right, angle_unit)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):  # унарные операции
        operand = evaluate(node.operand, angle_unit)
        return operators[type(node.op)](operand)
    elif isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name not in functions:
            raise ValueError(f"Неизвестная функция: {func_name}")
        
        args = [evaluate(arg, angle_unit) for arg in node.args]
        if len(args) != 1:
            raise ValueError(f"Функция {func_name} принимает ровно 1 аргумент")
        
        value = args[0]
        if func_name in ['sin', 'cos', 'tg', 'ctg'] and angle_unit == 'degree':
            value = math.radians(value)
        
        try:
            return functions[func_name](value)
        except ValueError as e:
            raise ValueError(f"Ошибка в функции {func_name}: {e}")
    elif isinstance(node, ast.Name):
        if node.id in constants:
            return constants[node.id]
        raise ValueError(f"Неизвестная константа: {node.id}")
    else:
        raise TypeError("Неверное выражение")

def calculate(expression, angle_unit='radian'):
    try:
        # Парсим выражение в AST
        if isinstance(expression, str):
            tree = parse(expression)
        else:
            tree = expression
        # Вычисляем результат
        result = evaluate(tree, angle_unit)
        # Проверяем полученный результат на переполнение
        if math.isinf(result) or math.isnan(result):
            raise OverflowError("Ошибка вычислителя: Арифметическое переполнение.")
        return result
    except (SyntaxError, TypeError, KeyError) as e:
        raise ValueError(f"Ошибка вычислителя: {e}")
    except ZeroDivisionError:
        raise ZeroDivisionError("Ошибка вычислителя: Деление на ноль.")
    except OverflowError:
        raise OverflowError("Ошибка вычислителя: Арифметическое переполнение.")

if __name__ == "__main__":
    args = parser.parse_args()  
    if not args.expression:
        parser.print_help()
        sys.exit(1)
    expression = args.expression
    try:
        result = calculate(expression, args.angle_unit)
        print(f"Результат: {result}")
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
