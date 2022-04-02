%option noyywrap
%option yylineno
%{
  #include "calc.tab.h"
  int yylex();
%}

%%
^#(.|\\\n)*\n   ;
\\\n            ;
[[:blank:]]+ 	;
[0-9]+	        { yylval = atoi(yytext); return NUM; }
"+"             { return PLUS; }
"-"             { return MINUS; }
"*"             { return MULT; }
"/"             { return DIV; }
"%"             { return MOD; }
"^"             { return POW; }
\(              { return LT_BR; }
\)              { return RT_BR; }
\n              { return EOL; }
.               { return ERROR; }
%%