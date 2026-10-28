"""Original classroom question bank; deterministic edge/stress cases and C++ references."""
from dataclasses import dataclass
from collections import deque
import random


@dataclass(frozen=True)
class Question:
    code: str
    title: str
    statement: str
    cases: tuple[tuple[str, str], ...]
    solution: str
    io_mode: str = "stdio"
    input_filename: str | None = None
    output_filename: str | None = None


def question(code, title, description, input_spec, output_spec, cases, solution, file_io=False):
    first = cases[0]
    statement = f"{description}\n\nDỮ LIỆU VÀO\n{input_spec}\n\nKẾT QUẢ\n{output_spec}\n\nVí dụ đầu vào:\n{first[0]}\nVí dụ kết quả:\n{first[1]}"
    if file_io:
        statement += "\nBài này đọc DATA.INP và ghi RESULT.OUT trong thư mục làm việc."
        solution = solution.replace("int main(){", 'int main(){freopen("DATA.INP","r",stdin);freopen("RESULT.OUT","w",stdout);', 1)
    return Question(code, title, statement, tuple(cases), "#include <bits/stdc++.h>\nusing namespace std;\n"+solution,
                    "file" if file_io else "stdio", "DATA.INP" if file_io else None, "RESULT.OUT" if file_io else None)


def algorithms():
    rng = random.Random(20261027)
    arrays = [[2, 3, -1], [0], [-5], [-8, -3, -9], [10**9] * 20,
              [rng.randint(-10**6,10**6) for _ in range(10000)], [5,-5,5,-5,5]]
    def array_cases(oracle):
        return [(f"{len(a)}\n"+" ".join(map(str,a))+"\n", oracle(a)) for a in arrays]
    def kadane(a):
        current = best = a[0]
        for x in a[1:]: current=max(x,current+x);best=max(best,current)
        return str(best)+"\n"
    texts = ["A man a plan a canal Panama", "Hello LAN", "", "1221", "a", "AbBa", "ab"*1000+"a"]
    brackets = ["([]{})", "", "([)]", "((", "]", "{}[]()", "("*2000+")"*2000]
    def balanced(text):
        stack=[]
        for c in text:
            if c in "([{": stack.append(c)
            elif not stack or stack.pop() != {")":"(","]":"[","}":"{"}[c]: return "NO\n"
        return "NO\n" if stack else "YES\n"
    search_cases=[]
    for a in [[1,2,2,4],[],[-3],list(range(0,20000,2)),[7]*100]:
        queries=[2,7,-3,0,19998,20000]
        import bisect
        output=[]
        for x in queries:
            index=bisect.bisect_left(a,x)
            output.append(str(index+1 if index<len(a) and a[index]==x else -1))
        search_cases.append((f"{len(a)} {len(queries)}\n"+" ".join(map(str,a))+"\n"+" ".join(map(str,queries))+"\n","\n".join(output)+"\n"))
    sums=[]
    for a in arrays:
        intervals=[(1,len(a)),(1,1),(len(a),len(a))]
        sums.append((f"{len(a)} {len(intervals)}\n"+" ".join(map(str,a))+"\n"+"".join(f"{l} {r}\n" for l,r in intervals),"".join(str(sum(a[l-1:r]))+"\n" for l,r in intervals)))
    interval_sets=[[(1,3),(2,6),(8,10)],[],[(1,1)],[(1,2),(2,3)],[(5,8),(1,10)],[(i,i+2) for i in range(1000)]]
    merged=[]
    for values in interval_sets:
        result=[]
        for left,right in sorted(values):
            if result and left<=result[-1][1]: result[-1][1]=max(result[-1][1],right)
            else: result.append([left,right])
        merged.append((str(len(values))+"\n"+"".join(f"{l} {r}\n" for l,r in values),str(len(result))+"\n"+"".join(f"{l} {r}\n" for l,r in result)))
    graphs=[(4,[(1,2),(2,4),(1,3)],1,4),(3,[(1,2)],1,3),(1,[],1,1),(4,[(1,2),(1,2),(2,3),(3,4)],1,4),(1000,[(i,i+1) for i in range(1,1000)],1,1000)]
    bfs=[]
    for n,edges,start,end in graphs:
        graph=[[] for _ in range(n+1)]
        for a,b in edges: graph[a].append(b);graph[b].append(a)
        distance=[-1]*(n+1);distance[start]=0;queue=deque([start])
        while queue:
            u=queue.popleft()
            for v in graph[u]:
                if distance[v]<0: distance[v]=distance[u]+1;queue.append(v)
        bfs.append((f"{n} {len(edges)} {start} {end}\n"+"".join(f"{a} {b}\n" for a,b in edges),str(distance[end])+"\n"))
    activities=[[(1,3),(2,5),(3,4),(4,6)],[],[(1,2)],[(0,100),(1,2),(2,3)],[(1,4),(1,3),(1,2)],[(i,i+1) for i in range(1000)]]
    schedule=[]
    for values in activities:
        count=0;end=-1
        for left,right in sorted(values,key=lambda x:(x[1],x[0])):
            if left>=end: count+=1;end=right
        schedule.append((str(len(values))+"\n"+"".join(f"{l} {r}\n" for l,r in values),str(count)+"\n"))
    return [
        question("A01","Tổng dãy số 64 bit","Tính tổng các phần tử của dãy số nguyên.","n (1..100000), sau đó n số trong [-10^9,10^9].","Một số nguyên là tổng dãy.",array_cases(lambda a:str(sum(a))+"\n"),r'int main(){int n;cin>>n;long long x,s=0;while(n--){cin>>x;s+=x;}cout<<s<<"\n";}'),
        question("A02","Đoạn con có tổng lớn nhất","Tìm tổng lớn nhất của một đoạn con liên tiếp không rỗng.","n (1..100000), sau đó n số trong [-10^9,10^9].","Tổng lớn nhất; dãy toàn âm vẫn phải chọn ít nhất một phần tử.",array_cases(kadane),r'int main(){int n;cin>>n;long long x,cur,best;cin>>x;cur=best=x;while(--n){cin>>x;cur=max(x,cur+x);best=max(best,cur);}cout<<best<<"\n";}'),
        question("A03","Sắp xếp và loại trùng","Liệt kê các giá trị khác nhau theo thứ tự tăng dần.","n (1..100000), sau đó n số trong [-10^9,10^9].","Dòng đầu số giá trị khác nhau; dòng sau các giá trị, cách nhau một dấu cách.",array_cases(lambda a:str(len(set(a)))+"\n"+" ".join(map(str,sorted(set(a))))+"\n"),r'int main(){int n;cin>>n;set<long long>s;long long x;while(n--){cin>>x;s.insert(x);}cout<<s.size()<<"\n";bool f=0;for(auto v:s){if(f)cout<<" ";cout<<v;f=1;}cout<<"\n";}'),
        question("A04","Chuỗi đối xứng","Bỏ ký tự không phải chữ/số ASCII, đổi về chữ thường rồi kiểm tra đối xứng. Chuỗi rỗng được coi là đối xứng.","Một dòng ASCII, dài 0..100000 ký tự.","YES hoặc NO.",[(s+"\n",("YES" if (t:=''.join(c.lower() for c in s if c.isalnum()))==t[::-1] else "NO")+"\n") for s in texts],r'int main(){string s,t;getline(cin,s);for(unsigned char c:s)if(isalnum(c))t+=tolower(c);string r=t;reverse(r.begin(),r.end());cout<<(r==t?"YES":"NO")<<"\n";}'),
        question("A05","Kiểm tra ngoặc bằng stack","Ngoặc phải đóng đúng loại và đúng thứ tự. Chuỗi rỗng hợp lệ.","Một dòng gồm các ký tự ()[]{}; dài 0..100000.","YES nếu hợp lệ, ngược lại NO.",[(s+"\n",balanced(s)) for s in brackets],r'int main(){string s;getline(cin,s);stack<char>st;bool ok=1;for(char c:s){if(c==40||c==91||c==123)st.push(c);else{char v=c==41?40:c==93?91:123;if(st.empty()||st.top()!=v){ok=0;break;}st.pop();}}cout<<((ok&&st.empty())?"YES":"NO")<<"\n";}'),
        question("A06","Tìm vị trí đầu tiên","Với mỗi truy vấn, tìm vị trí đầu tiên của giá trị trong dãy đã sắp xếp.","n q (0<=n<=100000,1<=q<=100000), n số tăng không giảm, q giá trị cần tìm; mọi giá trị trong [-10^9,10^9].","Mỗi truy vấn in chỉ số từ 1, hoặc -1 nếu không có.",search_cases,r'int main(){int n,q;cin>>n>>q;vector<long long>a(n);for(auto&x:a)cin>>x;while(q--){long long x;cin>>x;auto p=lower_bound(a.begin(),a.end(),x);cout<<((p!=a.end()&&*p==x)?p-a.begin()+1:-1)<<"\n";}}'),
        question("A07","Truy vấn tổng đoạn bằng file","Tiền xử lý prefix sum để trả lời tổng đoạn [L,R].","File DATA.INP: n q (1..100000), n số trong [-10^9,10^9], q dòng L R với 1<=L<=R<=n.","File RESULT.OUT: mỗi dòng một tổng đoạn 64 bit.",sums,r'int main(){int n,q;cin>>n>>q;vector<long long>s(n+1);for(int i=1;i<=n;i++){long long x;cin>>x;s[i]=s[i-1]+x;}while(q--){int l,r;cin>>l>>r;cout<<s[r]-s[l-1]<<"\n";}}',True),
        question("A08","Gộp các đoạn giao nhau","Các đoạn đóng giao nhau hoặc có chung đầu mút được gộp. Ví dụ [1,2] và [2,3] thành [1,3]; [1,2] và [3,4] giữ riêng.","n (0..100000), sau đó n dòng L R (0<=L<=R<=10^9).","Số đoạn sau gộp, tiếp theo các đoạn theo đầu trái tăng dần.",merged,r'int main(){int n;cin>>n;vector<pair<int,int>>a(n),b;for(auto&v:a)cin>>v.first>>v.second;sort(a.begin(),a.end());for(auto v:a){if(!b.empty()&&v.first<=b.back().second)b.back().second=max(b.back().second,v.second);else b.push_back(v);}cout<<b.size()<<"\n";for(auto v:b)cout<<v.first<<" "<<v.second<<"\n";}'),
        question("A09","Số cạnh ít nhất với BFS","Đồ thị vô hướng, không trọng số. Tìm số cạnh ít nhất từ s đến t; có thể có cạnh lặp.","n m s t (1<=n<=10000,0<=m<=100000), tiếp theo m cạnh u v; đỉnh đánh số 1..n.","Số cạnh ít nhất hoặc -1 nếu không tới được.",bfs,r'int main(){int n,m,s,t;cin>>n>>m>>s>>t;vector<vector<int>>g(n+1);while(m--){int a,b;cin>>a>>b;g[a].push_back(b);g[b].push_back(a);}vector<int>d(n+1,-1);queue<int>q;d[s]=0;q.push(s);while(!q.empty()){int u=q.front();q.pop();for(int v:g[u])if(d[v]<0){d[v]=d[u]+1;q.push(v);}}cout<<d[t]<<"\n";}'),
        question("A10","Chọn nhiều hoạt động nhất","Chọn số hoạt động tối đa không chồng thời gian. Hoạt động mới được bắt đầu đúng lúc hoạt động trước kết thúc.","n (0..100000), sau đó n dòng start end (0<=start<end<=10^9).","Số hoạt động tối đa.",schedule,r'int main(){int n;cin>>n;vector<pair<int,int>>a;while(n--){int l,r;cin>>l>>r;a.push_back({r,l});}sort(a.begin(),a.end());int end=-1,count=0;for(auto v:a)if(v.second>=end){count++;end=v.first;}cout<<count<<"\n";}'),
    ]


def fundamentals():
    import math
    pairs=[(2,3),(0,0),(-9,4),(-7,-8),(10**9,10**9),(1,-1)]
    values=[0,1,2,9,10,97,100,999983]
    return [
        question("P01","Tổng hai số nguyên","Tính tổng hai số nguyên a và b.","Hai số nguyên trong [-10^9,10^9].","Một số nguyên a+b.",[(f"{a} {b}\n",f"{a+b}\n") for a,b in pairs],r'int main(){long long a,b;cin>>a>>b;cout<<a+b<<"\n";}'),
        question("P02","Giá trị lớn nhất của ba số","Tìm số lớn nhất trong ba số nguyên.","Ba số nguyên trong [-10^9,10^9].","Giá trị lớn nhất.",[(f"{a} {b} {c}\n",f"{max(a,b,c)}\n") for a,b,c in [(1,2,3),(-8,-3,-9),(0,0,0),(7,7,1),(10**9,0,-10**9),(-2,5,5)]],r'int main(){long long a,b,c;cin>>a>>b>>c;cout<<max(a,max(b,c))<<"\n";}'),
        question("P03","Tổng từ 1 đến n","Tính 1+2+...+n; n=0 có tổng bằng 0.","n (0..10^9).","Tổng dạng số nguyên 64 bit.",[(f"{n}\n",f"{n*(n+1)//2}\n") for n in [0,1,2,10,100000,10**9]],r'int main(){long long n;cin>>n;cout<<n*(n+1)/2<<"\n";}'),
        question("P04","Giai thừa","Tính n! với quy ước 0!=1.","n (0..20).","Một số nguyên n!.",[(f"{n}\n",f"{math.factorial(n)}\n") for n in [0,1,2,5,12,20]],r'int main(){int n;cin>>n;long long f=1;for(int i=2;i<=n;i++)f*=i;cout<<f<<"\n";}'),
        question("P05","Tổng chữ số","Tính tổng các chữ số thập phân của n.","n (0..10^18).","Tổng chữ số.",[(f"{n}\n",f"{sum(map(int,str(n)))}\n") for n in [0,7,10,10001,999999999999999999,10**18]],r'int main(){long long n,s=0;cin>>n;while(n){s+=n%10;n/=10;}cout<<s<<"\n";}'),
        question("P06","Ước chung lớn nhất","Tính gcd(a,b), quy ước gcd(0,0)=0.","a,b (0..10^9).","Ước chung lớn nhất.",[(f"{a} {b}\n",f"{math.gcd(a,b)}\n") for a,b in [(12,18),(0,0),(0,7),(9,0),(999983,97),(10**9,10**9)]],r'int main(){long long a,b;cin>>a>>b;while(b){long long t=a%b;a=b;b=t;}cout<<a<<"\n";}'),
        question("P07","Kiểm tra số nguyên tố","Số nguyên tố là số lớn hơn 1 chỉ có hai ước dương.","n (0..10^9).","YES nếu n nguyên tố, ngược lại NO.",[(f"{n}\n",("YES" if n>=2 and all(n%d for d in range(2,math.isqrt(n)+1)) else "NO")+"\n") for n in values+[10**9]],r'int main(){long long n;cin>>n;bool ok=n>=2;for(long long d=2;d*d<=n;d++)if(n%d==0){ok=0;break;}cout<<(ok?"YES":"NO")<<"\n";}'),
        *[Question(**{**vars(q),"code":f"P{i:02d}"}) for i,q in enumerate([algorithms()[0],algorithms()[2],algorithms()[3]],8)],
    ]


def bank():
    return {"programming": fundamentals(), "algorithms": algorithms()}


def exam_groups(questions):
    return [("practice", "Luyện tập đầu khóa", questions[:2]),
            ("midterm", "Giữa kỳ 1 - Nền tảng", questions[:2]),
            ("midterm", "Giữa kỳ 2 - Vận dụng", questions[2:5]),
            ("final", "Cuối kỳ - Tổng hợp", questions[5:])]
