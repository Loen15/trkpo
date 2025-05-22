import sys
import ast
import operator as op
import argparse
import math
import re

# Парсер аргументов командной строки
parser = argparse.ArgumentParser(
    prog="python main.py",
    description="Вычисление выражений c поддержкой +, -, /, *")
parser.add_argument("expression", nargs="?", help="Математическое выражение для вычисления типа '1+1'")

operators = {
    ast.Add: op.add, # +
    ast.Sub: op.sub, # -
    ast.Mult: op.mul, # *
    ast.Div: op.truediv, # /
    ast.USub: op.neg, # унарный -
    ast.Pow: op.pow # возведение в степень  
}

def parse(expression):
    try:
        # Запрещаем пробелы между цифрами, в том числе вида 1e 10
        if re.search(r"\d\s+\d", expression) or re.search(r"e\s+\d", expression) or re.search(r"\d\s+e", expression):
            raise ValueError("Пробел между цифрами не допускается.")
        
        # Удаляем лишние пробелы
        expression = " ".join(expression.split())
        
        # Запрещаем символы кроме цифр и 'e'
        if any(c.isalpha() and c not in 'eE' for c in expression):
            raise ValueError("Выражение содержит неверные символы")
          
        # Заменяем ^ на ** для корректной работы
        expression = expression.replace('^', '**')
        
        # Преобразуем выражение в дерево AST
        tree = ast.parse(expression, mode='eval')
        return tree.body
    except (SyntaxError, TypeError, KeyError, ValueError) as e:
        raise ValueError(f"Ошибка парсера: Некорректное выражение: {e}")

def evaluate(node):
    #Рекурсивно обрабатываем AST-узлы
    if isinstance(node, ast.Constant): # числа 
        return node.value
    elif isinstance(node, ast.BinOp):  # бинарные операции
        left = evaluate(node.left)
        right = evaluate(node.right)
        return operators[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):  # унарные операции
        operand = evaluate(node.operand)
        return operators[type(node.op)](operand)
    else:
        raise TypeError("Ошибка вычислителя: Неверное выражение")

def calculate(expression):
    try:
        # Парсим выражение в AST
        if isinstance(expression, str):
            tree = parse(expression)
        else:
            tree = expression
        # Вычисляем результат
        result = evaluate(tree)
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
        result = calculate(expression)
        print(f"Результат: {result}")
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
