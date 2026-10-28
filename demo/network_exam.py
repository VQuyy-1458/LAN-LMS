"""Original networking practice problems; reference solutions are private to the repo."""
from dataclasses import dataclass
import heapq
import ipaddress


@dataclass(frozen=True)
class PracticeProblem:
    code: str
    title: str
    statement: str
    cases: tuple[tuple[str, str], ...]
    solution: str


def item(code, title, description, input_spec, output_spec, cases, solution):
    first = cases[0]
    statement = f"{title}\n\n{description}\n\nINPUT\n{input_spec}\n\nOUTPUT\n{output_spec}\n\nVÍ DỤ\nInput:\n{first[0]}\nOutput:\n{first[1]}\nBài thực hành mô phỏng dữ liệu mạng, không cần tạo socket trong bài làm."
    return PracticeProblem(code, title, statement, tuple(cases), "#include <bits/stdc++.h>\nusing namespace std;\n"+solution+"\n")


def problems():
    valid = ["192.168.1.1", "0.0.0.0", "255.255.255.255", "256.1.2.3", "1.2.3", "01.2.3.4", "1.2.3.-1", "10.0.0.1"]
    validity = [(str(len(a))+"\n"+"\n".join(a)+"\n", "\n".join("VALID" if _valid_ip(x) else "INVALID" for x in a)+"\n") for a in (valid[:3], valid[3:], valid, [valid[0]], ["1.2.3.4.5"], ["127.0.0.1", "1..2.3"])]
    ips = ["192.168.1.1", "0.0.0.0", "255.255.255.255", "128.0.0.0", "10.0.0.1", "1.2.3.4"]
    midterm = [
        item("M01", "Kiểm tra địa chỉ IPv4", "IPv4 hợp lệ có đúng 4 octet thập phân 0..255 ngăn bằng dấu chấm; không có dấu +/-, không có số 0 đứng đầu octet nhiều chữ số.", "n (1..1000), tiếp theo n chuỗi không có khoảng trắng, dài tối đa 100.", "Mỗi chuỗi in VALID hoặc INVALID trên một dòng.", validity,
             r'''int main(){int n;cin>>n;string s;while(n--){cin>>s;bool ok=true;int count=0;string part;stringstream ss(s);while(getline(ss,part,'.')){count++;if(part.empty()||part.size()>3||(part.size()>1&&part[0]=='0')){ok=false;continue;}int v=0;for(char c:part){if(c<'0'||c>'9')ok=false;else v=v*10+c-'0';}if(v>255)ok=false;}if(s.empty()||s.back()=='.'||count!=4)ok=false;cout<<(ok?"VALID":"INVALID")<<"\n";}}'''),
        item("M02", "Chuyển IPv4 sang số nguyên", "Biểu diễn IPv4 bằng số nguyên không dấu 32 bit theo thứ tự byte mạng: a*256^3+b*256^2+c*256+d.", "Một địa chỉ IPv4 hợp lệ.", "Số nguyên trong đoạn 0..4294967295.", [(x+"\n", str(int(ipaddress.IPv4Address(x)))+"\n") for x in ips],
             r'''int main(){string s;cin>>s;replace(s.begin(),s.end(),'.',' ');stringstream in(s);unsigned long long v=0,a;while(in>>a)v=v*256+a;cout<<v<<"\n";}'''),
        item("M03", "Nhận diện cổng dịch vụ", "Bảng phân loại: 21 FTP, 22 SSH, 53 DNS, 80 HTTP, 443 HTTPS; cổng còn lại là OTHER.", "n (1..1000), sau đó n số cổng trong 0..65535.", "Mỗi cổng in tên dịch vụ trên một dòng.", _port_cases(),
             r'''int main(){int n,p;cin>>n;map<int,string>m={{21,"FTP"},{22,"SSH"},{53,"DNS"},{80,"HTTP"},{443,"HTTPS"}};while(n--){cin>>p;cout<<(m.count(p)?m[p]:"OTHER")<<"\n";}}'''),
        item("M04", "Tổng kích thước bản tin", "Máy chủ nhận n bản tin. Tính tổng số byte payload để thống kê lưu lượng, không tính header.", "n (1..100000), tiếp theo n kích thước 0..10^9 byte.", "Tổng số byte, dùng số nguyên 64 bit.", [(str(len(a))+"\n"+" ".join(map(str,a))+"\n", str(sum(a))+"\n") for a in ([12,8,20], [0], [10**9]*10, [1,0,1], [65535,65536], list(range(100)))],
             r'''int main(){int n;cin>>n;long long sum=0,x;while(n--){cin>>x;sum+=x;}cout<<sum<<"\n";}'''),
        item("M05", "Phân loại mã trạng thái HTTP", "100..199: INFORMATIONAL; 200..299: SUCCESS; 300..399: REDIRECTION; 400..499: CLIENT_ERROR; 500..599: SERVER_ERROR. Ngoài 100..599 là INVALID.", "n (1..1000), sau đó n số nguyên 0..999.", "Mỗi mã in một nhóm trên một dòng.", _http_cases(),
             r'''int main(){int n,x;cin>>n;string a[]={"INVALID","INFORMATIONAL","SUCCESS","REDIRECTION","CLIENT_ERROR","SERVER_ERROR"};while(n--){cin>>x;cout<<((x>=100&&x<=599)?a[x/100]:"INVALID")<<"\n";}}''')
    ]
    networks = [("192.168.1.20",24,"192.168.1.99"), ("192.168.1.20",24,"192.168.2.1"), ("10.1.2.3",0,"255.255.255.255"), ("10.1.2.3",32,"10.1.2.3"), ("10.1.2.3",32,"10.1.2.4"), ("172.16.255.255",16,"172.16.0.1")]
    frames = ["3:cat5:hello", "1:a1:b1:c", "0:", "10:abcdefghij", "3:ab", "abc", "2:ab4:test", ""]
    words = [[1,2,3], [65535], [0], [65535,65535,1], [32768,32768], [65535]*100]
    final = [
        item("F01", "Kiểm tra cùng subnet", "Hai máy cùng subnet nếu p bit cao nhất của IPv4 giống nhau. Với p=0 mọi địa chỉ cùng subnet; p=32 phải giống hoàn toàn.", "Một dòng gồm IPv4_A, p (0..32), IPv4_B. Các địa chỉ đều hợp lệ.", "YES nếu cùng subnet, ngược lại NO.", [(f"{a} {p} {b}\n", ("YES" if ipaddress.IPv4Address(b) in ipaddress.IPv4Network(f"{a}/{p}", strict=False) else "NO")+"\n") for a,p,b in networks],
             r'''unsigned long long ip(string s){replace(s.begin(),s.end(),'.',' ');stringstream in(s);unsigned long long a,v=0;while(in>>a)v=v*256+a;return v;}int main(){string a,b;int p;cin>>a>>p>>b;cout<<((p==0||(ip(a)>>(32-p))==(ip(b)>>(32-p)))?"YES":"NO")<<"\n";}'''),
        item("F02", "TTL qua các router", "Mỗi router làm TTL giảm 1. Sau h router, gói chỉ còn hợp lệ nếu TTL cuối lớn hơn 0.", "Hai số ttl (1..255) và h (0..1000000000).", "In TTL còn lại nếu lớn hơn 0, hoặc EXPIRED.", [(f"{ttl} {h}\n", str(ttl-h)+"\n" if ttl>h else "EXPIRED\n") for ttl,h in ((64,3),(1,0),(1,1),(64,64),(255,1000000000),(255,254))],
             r'''int main(){long long ttl,h;cin>>ttl>>h;if(ttl>h)cout<<ttl-h<<"\n";else cout<<"EXPIRED\n";}'''),
        item("F03", "Tách khung bản tin TCP", "TCP là luồng byte, không giữ ranh giới bản tin. Giao thức ghép khung L:payload. L là số ký tự payload, viết thập phân, không có 0 đứng đầu trừ chính số 0. Payload chỉ gồm chữ ASCII và số. Toàn bộ luồng phải được phân tích hết.", "Một dòng dài 0..100000 ký tự. L trong 0..100000. Dòng rỗng biểu diễn không có bản tin.", "Nếu sai, chỉ in INVALID. Nếu đúng, in số bản tin, sau đó mỗi payload trên một dòng (payload rỗng là dòng rỗng).", [(s+"\n", _frames(s)) for s in frames],
             r'''int main(){string s;getline(cin,s);vector<string>a;size_t i=0;bool ok=true;while(i<s.size()){size_t j=i;long long n=0;while(i<s.size()&&isdigit((unsigned char)s[i])){n=n*10+s[i++]-'0';if(n>100000){ok=false;break;}}if(!ok||j==i||(i-j>1&&s[j]=='0')||i>=s.size()||s[i++]!=':'||n>(long long)(s.size()-i)){ok=false;break;}string v=s.substr(i,n);for(char c:v)if(!isalnum((unsigned char)c))ok=false;if(!ok)break;a.push_back(v);i+=n;}if(!ok)cout<<"INVALID\n";else{cout<<a.size()<<"\n";for(auto &v:a)cout<<v<<"\n";}}'''),
        item("F04", "Checksum bù một 16 bit", "Cộng các từ 16 bit; nếu tổng có phần vượt 16 bit, cộng phần tràn vào 16 bit thấp, lặp đến khi hết tràn. Checksum là bù một của tổng 16 bit.", "n (1..100000), tiếp theo n số nguyên 0..65535.", "Checksum thập phân trong 0..65535.", [(str(len(a))+"\n"+" ".join(map(str,a))+"\n", str(_checksum(a))+"\n") for a in words],
             r'''int main(){int n;cin>>n;unsigned long long s=0,x;while(n--){cin>>x;s+=x;}while(s>>16)s=(s&65535)+(s>>16);cout<<((~s)&65535)<<"\n";}'''),
        item("F05", "Độ trễ đường truyền ngắn nhất", "Mạng có n router và m đường truyền hai chiều với độ trễ dương. Tìm tổng độ trễ nhỏ nhất từ s đến t. Có thể có nhiều cạnh cùng cặp router.", "Dòng đầu n m s t (1<=n<=1000, 0<=m<=10000, router đánh số 0..n-1). Tiếp theo m dòng u v w (1<=w<=10^9).", "Tổng độ trễ nhỏ nhất, hoặc -1 nếu không tới được; s=t in 0.", _route_cases(),
             r'''int main(){int n,m,s,t;cin>>n>>m>>s>>t;vector<vector<pair<int,long long>>>g(n);while(m--){int u,v;long long w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}vector<long long>d(n,LLONG_MAX);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[s]=0;q.push({0,s});while(!q.empty()){auto[x,u]=q.top();q.pop();if(x!=d[u])continue;for(auto[v,w]:g[u])if(d[v]>x+w){d[v]=x+w;q.push({d[v],v});}}cout<<(d[t]==LLONG_MAX?-1:d[t])<<"\n";}''')
    ]
    return {"midterm": midterm, "final": final}


def _valid_ip(value):
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False


def _port_cases():
    names = {21:"FTP",22:"SSH",53:"DNS",80:"HTTP",443:"HTTPS"}
    return [(str(len(a))+"\n"+" ".join(map(str,a))+"\n", "\n".join(names.get(x,"OTHER") for x in a)+"\n") for a in ([80,443,53], [21,22], [0,65535,8080], [80], [443]*10, list(range(60,85)))]


def _http_cases():
    labels = ["INVALID","INFORMATIONAL","SUCCESS","REDIRECTION","CLIENT_ERROR","SERVER_ERROR"]
    return [(str(len(a))+"\n"+" ".join(map(str,a))+"\n", "\n".join(labels[x//100] if 100<=x<=599 else "INVALID" for x in a)+"\n") for a in ([200,404,500], [100,199,299,399,499,599], [0,99,600,999], [204], [301,302,307], [400,401,403,502])]


def _frames(value):
    result=[]
    while value:
        length, separator, tail = value.partition(":")
        if not separator or not length.isascii() or not length.isdecimal() or len(length)>6 or (len(length)>1 and length[0]=="0"):
            return "INVALID\n"
        size=int(length)
        if size>100000 or size>len(tail) or any(not c.isascii() or not c.isalnum() for c in tail[:size]):
            return "INVALID\n"
        result.append(tail[:size]); value=tail[size:]
    return str(len(result))+"\n"+"".join(s+"\n" for s in result)


def _checksum(words):
    total=sum(words)
    while total>>16:
        total=(total&65535)+(total>>16)
    return (~total)&65535


def _route_cases():
    cases=[(4,[(0,1,5),(1,3,6),(0,2,2),(2,3,3)],0,3), (3,[(0,1,4)],0,2), (1,[],0,0), (3,[(0,1,10**9),(1,2,10**9)],0,2), (2,[(0,1,9),(0,1,2)],0,1), (4,[(0,1,1),(1,2,1),(2,3,1),(0,3,100)],0,3)]
    result=[]
    for n,edges,s,t in cases:
        graph=[[] for _ in range(n)]
        for u,v,w in edges:
            graph[u].append((v,w)); graph[v].append((u,w))
        distance=[float("inf")]*n; distance[s]=0; queue=[(0,s)]
        while queue:
            value,u=heapq.heappop(queue)
            if value!=distance[u]: continue
            for v,w in graph[u]:
                if value+w<distance[v]:
                    distance[v]=value+w; heapq.heappush(queue,(value+w,v))
        result.append((f"{n} {len(edges)} {s} {t}\n"+"".join(f"{u} {v} {w}\n" for u,v,w in edges), str(distance[t] if distance[t]!=float('inf') else -1)+"\n"))
    return result
