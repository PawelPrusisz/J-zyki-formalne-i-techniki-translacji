#include <iostream>
#include <fstream>
using namespace std;

string readFrom(string name)
{
    fstream my_file;
    string ans = "";
	my_file.open(name, ios::in);
	if (!my_file)
    {
		cout << "No such file";
	}
	else
    {
		string ch;
		while (true)
        {
			my_file >> ch;
			ans += ch;
            ans += " ";
            if (my_file.eof())
				break;
		}

	}
	my_file.close();
	return ans;
}

int getNextState(string pattern, int M, int state, int x)
{
    if (state < M && x == pattern[state])
    {
        return state+1;
    }
        
 
    for (int ns = state; ns > 0; ns--)
    {
        if (pattern[ns-1] == x)
        {
            int i;
            for (i = 0; i < ns-1; i++)
            {
                if (pattern[i] != pattern[state-ns+1+i])break;
            }
            if (i == ns-1)return ns;
        }
    }
 
    return 0;
}

void computeTF(string pattern, int M, int TF[][256])
{
    int state, x;
    for (state = 0; state <= M; ++state)
    {
        for (x = 0; x < 256; ++x)
        {
            TF[state][x] = getNextState(pattern, M, state, x);
        }            
    }
        
}

void search(string pattern, string txt)
{
    int M = pattern.size();
    int N = txt.size();
 
    int TF[M+1][256];
 
    computeTF(pattern, M, TF);

     int state=0;
    for (int i = 0; i < N; i++)
    {
        state = TF[state][txt[i]];
        if (state == M)
        {
            cout<<"Znaleziono pattern na pozycji "<< i-M+1<<"\n";
        }
    }
}
int main(int argc, char* argv[])
{
    string pattern = argv[1];
    string fileName = argv[2];
    string fileContent = readFrom(fileName);

    search(pattern, fileContent);
    return 0;
}