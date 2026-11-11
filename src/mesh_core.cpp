// Portable replacement for the geometry operations in the Yong CHEN (12/05)
// MeshTestbed teaching project. Original MFC application remains alongside this.
#include "mesh_core.h"
#include "mesh_internal.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <limits>
#include <locale>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cerrno>
#include <cstdlib>
#include <locale.h>

namespace meshcore {
thread_local std::string error;
void topology(Mesh& m) {
    m.reverse.assign(m.f.size()*3,-1);
    std::map<std::pair<int64_t,int64_t>,std::vector<int64_t>> edges;
    for(size_t i=0;i<m.f.size();++i) for(int c=0;c<3;++c) {
        auto a=m.f[i][c], b=m.f[i][(c+1)%3];
        edges[{std::min(a,b),std::max(a,b)}].push_back(static_cast<int64_t>(i*3+c));
    }
    for(const auto& entry:edges) {
        const auto& es=entry.second;
        if(es.size()==1 && entry.first.first!=entry.first.second) continue;
        if(es.size()==2 && entry.first.first!=entry.first.second) {
            auto a=es[0],b=es[1];
            if(m.f[a/3][a%3]==m.f[b/3][(b%3+1)%3]) {m.reverse[a]=b;m.reverse[b]=a;continue;}
        }
        for(auto e:es) m.reverse[e]=-2;
    }
}
uint32_t u32(const unsigned char* p) { return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24); }
double f32(const unsigned char* p) { uint32_t u=u32(p); float f; std::memcpy(&f,&u,4); return f; }
// Tokenize ASCII explicitly rather than consulting the process CRT ctype table.
// A private numeric locale also isolates parsing from Python/extension locale changes.
struct AsciiReader {
    const unsigned char* data;size_t size,pos=0;
#ifdef _WIN32
    _locale_t locale=_create_locale(LC_NUMERIC,"C");
    ~AsciiReader() {if(locale) _free_locale(locale);}
#else
    locale_t locale=newlocale(LC_NUMERIC_MASK,"C",nullptr);
    ~AsciiReader() {if(locale) freelocale(locale);}
#endif
    static bool space(unsigned char c) {return c==' '||c=='\t'||c=='\r'||c=='\n'||c=='\v'||c=='\f';}
    std::string token() {
        while(pos<size&&space(data[pos])) ++pos;
        size_t begin=pos;while(pos<size&&!space(data[pos])) ++pos;
        return std::string(reinterpret_cast<const char*>(data+begin),pos-begin);
    }
    void line() {while(pos<size&&data[pos]!='\n') ++pos;if(pos<size) ++pos;}
    void expect(const char* expected) {
        auto word=token();if(word!=expected) throw std::runtime_error(std::string("Malformed STL: expected ")+expected+", got "+word);
    }
    double number() {
        require(locale,"Cannot create numeric locale");auto text=token();char* end=nullptr;errno=0;
#ifdef _WIN32
        double value=_strtod_l(text.c_str(),&end,locale);
#else
        double value=strtod_l(text.c_str(),&end,locale);
#endif
        require(!text.empty()&&end==text.c_str()+text.size()&&errno!=ERANGE&&std::isfinite(value),"Invalid STL number");
        return value;
    }
};
std::unique_ptr<Mesh> stl(const unsigned char* data,size_t size) {
    require(data && size,"Empty STL");
    auto m=std::make_unique<Mesh>();
    std::map<V,int64_t> ids;
    auto add=[&](const std::array<V,3>& triangle) {
        F f;
        for(int c=0;c<3;++c) { finite(triangle[c]);
            auto it=ids.emplace(triangle[c],static_cast<int64_t>(m->v.size()));
            if(it.second) m->v.push_back(triangle[c]);
            f[c]=it.first->second;
        }
        m->f.push_back(f);
    };
    const uint64_t n=size>=84?u32(data+80):0;
    // Some exporters append a four-byte checksum (the supplied cube does).
    if(size>=84 && n>0 && uint64_t(size)>=84+50*n) {
        require(n>0,"STL has no triangles");
        for(uint64_t i=0;i<n;++i) {
            std::array<V,3> t;
            const auto p=data+84+50*i+12;
            for(int c=0;c<3;++c) for(int k=0;k<3;++k) t[c][k]=f32(p+c*12+k*4);
            add(t);
        }
    } else {
        AsciiReader in{data,size};std::string word;
        in.expect("solid");in.line();
        bool ended=false;
        while(!(word=in.token()).empty()) {
            if(word=="endsolid") {in.line();ended=true;break;}
            require(word=="facet","Expected STL facet");in.expect("normal");
            for(int k=0;k<3;++k) in.number();
            in.expect("outer");in.expect("loop");std::array<V,3> t;
            for(auto& p:t) {in.expect("vertex");for(auto& x:p) x=in.number();}
            in.expect("endloop");in.expect("endfacet");add(t);
        }
        require(ended && !m->f.empty(),"Missing endsolid or empty STL");
        require(in.token().empty(),"Unexpected data after endsolid");
    }
    topology(*m); return m;
}
}
using namespace meshcore;
extern "C" {
int mc_abi_version(void) { return 2; }
const char* mc_last_error(void) { return error.c_str(); }
void mc_destroy(void* p) { delete static_cast<Mesh*>(p); }
int mc_from_stl(const unsigned char* data,size_t bytes,void** out) {
    if(out) *out=nullptr;
    return guard([&]{require(out,"Null output handle");auto m=stl(data,bytes);*out=m.release();});
}
int mc_from_arrays(const double* vertices,size_t nv,const int64_t* faces,size_t nf,void** out) {
    if(out) *out=nullptr;
    return guard([&]{
        require(out && vertices && faces && nv && nf,"Empty or null mesh arrays");
        require(nv<=size_t(INT64_MAX)/3 && nf<=size_t(INT64_MAX)/3,"Mesh too large");
        auto m=std::make_unique<Mesh>();m->v.resize(nv);m->f.resize(nf);
        for(size_t i=0;i<nv;++i) { for(int k=0;k<3;++k) m->v[i][k]=vertices[3*i+k];finite(m->v[i]); }
        for(size_t i=0;i<nf;++i) for(int k=0;k<3;++k) {
            auto v=faces[3*i+k];require(v>=0 && uint64_t(v)<nv,"Face index out of range");m->f[i][k]=v;
        }
        topology(*m);*out=m.release();
    });
}
int mc_counts(void* p,size_t* nv,size_t* nf) {return guard([&]{auto& m=get(p);require(nv&&nf,"Null count output");*nv=m.v.size();*nf=m.f.size();});}
int mc_copy_mesh(void* p,double* v,size_t vs,int64_t* f,size_t fs) {
    return guard([&]{auto& m=get(p);require(v&&f&&vs>=m.v.size()*3&&fs>=m.f.size()*3,"Output buffer too small");
        for(size_t i=0;i<m.v.size();++i) std::copy(m.v[i].begin(),m.v[i].end(),v+3*i);
        for(size_t i=0;i<m.f.size();++i) std::copy(m.f[i].begin(),m.f[i].end(),f+3*i);
    });
}
int mc_copy_reverse(void* p,int64_t* r,size_t n) {return guard([&]{auto& m=get(p);require(r&&n>=m.reverse.size(),"Output buffer too small");std::copy(m.reverse.begin(),m.reverse.end(),r);});}
int mc_metrics(void* p,double* o,size_t n,size_t* t,size_t tn) {
    return guard([&]{auto& m=get(p);require(o&&n>=8&&t&&tn>=3,"Output buffer too small");
        std::fill(o,o+8,0);std::fill(t,t+3,0);
        for(int k=0;k<3;++k) o[2+k]=o[5+k]=m.v[0][k];
        for(const auto& v:m.v) for(int k=0;k<3;++k) {o[2+k]=std::min(o[2+k],v[k]);o[5+k]=std::max(o[5+k],v[k]);}
        // Reference near the mesh improves closed-surface volume stability after translation.
        const V ref=m.v[0];long double area=0,volume=0;
        for(const auto& f:m.f) {
            const auto& a=m.v[f[0]];const auto& b=m.v[f[1]];const auto& c=m.v[f[2]];
            auto normal=cross(sub(b,a),sub(c,a));double ar=std::hypot(normal[0],normal[1],normal[2])*0.5;
            require(std::isfinite(ar),"Geometry overflow");area+=ar;if(ar==0) ++t[2];
            volume+=static_cast<long double>(dot(sub(a,ref),cross(sub(b,ref),sub(c,ref))))/6;
        }
        o[0]=static_cast<double>(area);o[1]=static_cast<double>(volume);
        require(std::isfinite(o[0])&&std::isfinite(o[1]),"Metric overflow");
        for(auto r:m.reverse) {if(r==-1) ++t[0];if(r==-2) ++t[1];}
    });
}
int mc_transform(void* p,const double* a) {
    return guard([&]{auto& m=get(p);require(a,"Null matrix");for(int i=0;i<16;++i) require(std::isfinite(a[i]),"Non-finite matrix");
        require(a[12]==0 && a[13]==0 && a[14]==0 && a[15]==1,"Only affine 4x4 matrices are supported");
        auto next=m.v;
        for(size_t i=0;i<next.size();++i) {for(int k=0;k<3;++k) next[i][k]=a[4*k]*m.v[i][0]+a[4*k+1]*m.v[i][1]+a[4*k+2]*m.v[i][2]+a[4*k+3];finite(next[i]);}
        m.v.swap(next); m.tree.clear(); m.order.clear();
    });
}
}
