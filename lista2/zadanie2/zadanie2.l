%{
#include<stdio.h>
int yylex();
int yywrap();
%}

%x COMMENT
%x CDATA
%x STRING

%%

\<!--           BEGIN(COMMENT);
<COMMENT>{
.|\n            ;
-->             BEGIN(INITIAL);
}

\<!--.*--.*-->  ECHO;

\<!\[CDATA\[    { ECHO; BEGIN(CDATA); }
<CDATA>{
.|\n            ECHO;
]]>             { ECHO; BEGIN(INITIAL); }
}

\"              { ECHO; BEGIN(STRING); }
<STRING>{
\"              { ECHO; BEGIN(INITIAL); }
.               ECHO;
}

%%

int yywrap() {
    return 1;
}

int main() {
    return yylex();
}