# class ListStack:
#     def __init__(self):
#         self.data = []
#
#     def push(self, val):
#         self.data.append(val)
#
#     def pop(self):
#         if self.is_empty():
#             raise IndexError("栈空，无法弹出")
#         return self.data.pop()
#
#     def top(self):
#         if self.is_empty():
#             raise IndexError("栈空，无栈顶元素")
#         return self.data[-1]
#
#     def is_empty(self):
#         return len(self.data) == 0
#
#
# def infix_to_postfix(expression):
#     precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '(': 0}
#     result = ""
#     operator_stack = ListStack()
#     print("===== 中缀转后缀过程 =====")
#     print(f"{'字符':<6}{'输出串':<12}{'运算符栈'}")
#     print("-" * 35)
#
#     for c in expression:
#         if c.isalnum():
#             result += c
#         elif c == '(':
#             operator_stack.push(c)
#         elif c == ')':
#             while operator_stack.top() != '(':
#                 result += operator_stack.pop()
#             operator_stack.pop()
#         else:
#             while not operator_stack.is_empty() and precedence[c] <= precedence[operator_stack.top()]:
#                 result += operator_stack.pop()
#             operator_stack.push(c)
#         # 打印当前这一步状态
#         print(f"{c:<6}{result:<12}{operator_stack.data}")
#
#     # 遍历完，弹出栈中剩余运算符
#     while not operator_stack.is_empty():
#         op = operator_stack.pop()
#         result += op
#         print(f"{op:<6}{result:<12}{operator_stack.data}")
#     return result
#
#
# def evaluate(post_expression):
#     stack = ListStack()
#     print("\n===== 后缀表达式求值过程 =====")
#     print(f"{'字符':<6}{'求值栈':<20}{'运算说明'}")
#     print("-" * 40)
#     for c in post_expression:
#         note = ""
#         if c.isdigit():
#             stack.push(int(c))
#         else:
#             right = stack.pop()
#             left = stack.pop()
#             if c == '+':
#                 res = left + right
#                 note = f"{left}+{right}={res}"
#             elif c == '-':
#                 res = left - right
#                 note = f"{left}-{right}={res}"
#             elif c == '*':
#                 res = left * right
#                 note = f"{left}*{right}={res}"
#             elif c == '/':
#                 res = left / right
#                 note = f"{left}/{right}={res}"
#             else:
#                 raise ValueError("不支持该运算符")
#             stack.push(res)
#         print(f"{c:<6}{str(stack.data):<20}{note}")
#     return stack.pop()
#
#
# if __name__ == '__main__':
#     expression = "(1+5)*(8-6)-((5-3)*2)"
#     post_expression = infix_to_postfix(expression)
#     res = evaluate(post_expression)
#     print("\n===== 最终结果 =====")
#     print('中缀表达式：', expression)
#     print('后缀表达式：', post_expression)
#     print('计算结果：', res)
def factorial(n):
    print(f"进入 factorial({n})")
    if n == 0 or n == 1:
        print(f"factorial({n}) 返回 1")
        return 1
    else:
        res = n * factorial(n - 1)
        print(f"factorial({n}) 返回 {n} * factorial({n-1}) = {res}")
        return res


if __name__ == '__main__':
    print("结果：", factorial(5))
