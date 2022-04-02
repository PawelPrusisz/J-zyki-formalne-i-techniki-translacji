%{

#include <math.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

int yylex (void);
int yyerror (char const *);
int p1 = 1234577;
int p2 = 1234576;



extern int yylineno;
bool error = false;
char onp[256];

void print_err (char *err)
{
    printf("Error in line %d : %s\n", yylineno-1, err);
    error = true;
}

int fix(long long a, int P)
{
    if(a < 0) return P + a%P;
    else return a%P;
}

int revers(long long a, int P)
{
    for(long long i = 1; i < P; i++)
    {
        if((i*a)%P == 1) 
        {
            return i;
        }
    }
    print_err("There is no reverse");
    return 0;
}

int add(long long a, long long b, int P)
{
    return fix(a+b, P);
}

int sub(long long a, long long b, int P)
{
    return fix(a-b, P);
}

int mult(long long a, long long b, int P)
{
    return fix(a*b, P);
}

int divide (long long a, long long b, int P)
{
    return fix(a*revers(b, P), P);
}

int modulo (long long a, long long b, int P)
{
    return fix(a % b, P);
}

int power(long long a, long long b, int P)
{
    int ans = 1;
    for(int i = 0; i < b; i++)
    {
        ans *= a;
        ans %= P;
    }
    return fix(ans, P);
}




%}


%define api.value.type {int}
%token NUM RT_BR LT_BR
%left PLUS MINUS
%left MULT DIV MOD
%nonassoc POW
%precedence NEG
%token EOL ERROR

%% 

input:
  %empty
  | input line
;


line:
  exp EOL  { if(!error) printf ("%s\n= %d \n\n",onp ,$1); error = false; memset(onp,0,strlen(onp));}
  | error EOL {printf("Syntax error in line %d \n\n", yylineno-1); error = false; memset(onp,0,strlen(onp));}
;


exp:      NUM                       { $$ = fix($1, p1); char *s; sprintf(s, "%d", fix($1, p1)); strcat(onp,s); strcat(onp," ");}
        | MINUS NUM                 { $$ = fix(-$2, p1);  char *s; sprintf(s, "%d", fix(-$2, p1)); strcat(onp,s); strcat(onp, " ");}
        | MINUS LT_BR exp RT_BR     { $$ = fix(-$3, p1); strcat(onp,"~ ");}
        | LT_BR exp RT_BR  { $$ = $2; }
        | exp PLUS exp     { $$ = add($1, $3, p1); strcat(onp,"+ "); }
        | exp MINUS exp    { $$ = sub($1, $3, p1); strcat(onp,"- "); }
        | exp MULT exp     { $$ = mult($1, $3, p1); strcat(onp,"* "); }
        | exp DIV exp      { if($3 == 0) {print_err("Can't divide by zero");} else {$$ = divide($1,$3, p1); strcat(onp,"/ ");}}
        | exp POW expres   { $$ = power($1, $3, p1); strcat(onp,"^ ");}
;


expres:  NUM                      { $$ = fix($1, p2); char *s; sprintf(s, "%d", fix($1, p2)); strcat(onp,s); strcat(onp," ");}
        | MINUS NUM                { $$ = fix(-$2, p2); char *s; sprintf(s, "%d", fix(-$2, p2)); strcat(onp,s); strcat(onp, " ");}
        | MINUS LT_BR expres RT_BR    { $$ = fix(-$3, p2); strcat(onp,"~ ");}
        | LT_BR expres RT_BR          { $$ = $2; }
        | expres PLUS expres       { $$ = add($1, $3, p2); strcat(onp,"+ "); }
        | expres MINUS expres      { $$ = sub($1, $3, p2); strcat(onp,"- "); } 
        | expres MULT expres       { $$ = mult($1, $3, p2); strcat(onp,"* "); }
        | expres DIV expres        { if($3 == 0) {print_err("Can't divide by zero");} else {$$ = divide($1,$3, p2); strcat(onp,"/ ");}}
;
%%

int yyerror(char const *s){return 1;}

int main()
{
    strcpy(onp,"");
    yyparse();
    return 0;
    
}