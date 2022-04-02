%{
#include <bits/stdc++.h>

using namespace std;

stack<int> calc_stack;
string error = "";

void handle_error(string error_message)
{
  error = error_message;
  calc_stack = stack<int>();
}

int add(int a, int b) 
{ 
    return a + b; 
}

int sub(int a, int b)
{ 
    return a - b;
}

int mul(int a, int b)
{ 
    return a * b;
}

int mod(int a, int b)
{
    if (b != 0)
    {
        return a % b;
    }
    else
    {
        handle_error("Błąd: dzielenie przez 0");
    }
}

int power(int a, int b)
{
    return pow(a, b);
}

int divide(int a, int b) 
{
    if (b != 0)
    {
        return a / b;
    }
    else
    {
        handle_error("Błąd: dzielenie przez 0");
    }
}

void calc(int (*operation)(int, int))
{
    if(calc_stack.size() > 1)
    {
        int a = calc_stack.top();
        calc_stack.pop();
        int b = calc_stack.top();
        calc_stack.pop();
        calc_stack.push(operation(b, a));
    }
    else
    {
        handle_error("Błąd: za mała liczba argumentów");
    }
}

void result()
{
    if(calc_stack.size() > 1)
    {
        handle_error("Błąd: za mała liczba argumentów");
    }
    if(calc_stack.size() == 1 && error == "")
    {
        cout << "= " << calc_stack.top() << "\n";
        calc_stack.pop();
    }
    else 
    {
        cout << error << "\n";
        error = "";
    }
}

%}

%x ERROR

%%

\-?[0-9]+   {calc_stack.push(stoi(yytext));}
\+          calc(&add);
\-          calc(&sub);
\*          calc(&mul);
\/          calc(&divide);
\%          calc(&mod);
\^          calc(&power);
\n          result();
" "         ;
.           { handle_error(string("Zły symbol ") + yytext); BEGIN(ERROR); }
<ERROR>{
  .|\n      BEGIN(0);
}
%%

int yywrap() {
    return 1;

}

int main() {
    return yylex();
}