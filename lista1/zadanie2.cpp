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

void KMP(string pattern, string text)
{
    int lps[pattern.size()];

    //LPS
    int len = 0;
  
    lps[0] = 0; 
  
    int i = 1;
    while (i < pattern.size()) {
        if (pattern[i] == pattern[len]) {
            len++;
            lps[i] = len;
            i++;
        }
        else 
        {
            
            if (len != 0) {
                len = lps[len - 1];
  
                
            }
            else 
            {
                lps[i] = 0;
                i++;
            }
        }
    }
    
    //KNP
    i = 0;
    int j = 0;
    while(i < text.size())
    {
        if(pattern[j] == text[i])
        {
            j++;
            i++;
        }
        if(j == pattern.size())
        {
            cout<<"Znaleziono pattern na pozycji "<<i - j<<"\n";
            j = lps[j - 1];
        }
        else if(i < text.size() && pattern[j] != text[i])
        {
            if(j != 0)
            {
                j = lps[j - 1];
            }
            else
            {
                i += 1;
            }
        }
    }

}

int main(int argc, char* argv[])
{
    string pattern = argv[1];
    string fileName = argv[2];
    string fileContent = readFrom(fileName);

    KMP(pattern, fileContent);

    return 0;
}