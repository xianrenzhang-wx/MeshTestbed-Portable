#include "mesh_core.h"
#include "mesh_internal.h"
#include <map>
#include <limits>
using namespace meshcore;
extern "C" {
const char* mc_version(void) { return "2.1.0"; }
int mc_tetra_classify(const double* vertices,const double* points,size_t n,double eps,double degen,
                     int* states,size_t ns,double* weights,size_t nw) {
 return guard([&]{
    tolerance(eps);tolerance(degen);
    require(vertices&&points&&states&&weights,"Null buffer");
    require(n<=ns&&n<=nw/4,"Output buffer too small");
    V v[4];for(size_t j=0;j<4;++j)v[j]=read3(vertices+3*j);
    double length=0;
    for(int i=0;i<4;++i)for(int j=0;j<i;++j)length=std::max(length,norm(sub(v[i],v[j])));
    require(std::isfinite(length),"Coordinate range overflow");
    V a{},b{},c{};double determinant=0;
    if(length>0){
      a=mul(sub(v[1],v[0]),1/length);b=mul(sub(v[2],v[0]),1/length);c=mul(sub(v[3],v[0]),1/length);
      finite(a);finite(b);finite(c);determinant=dot(a,cross(b,c));
    }
    for(size_t i=0;i<n;++i){
      V p=read3(points+3*i);double* w=weights+4*i;
      if(length==0||std::abs(determinant)<=degen){
        states[i]=2;std::fill(w,w+4,std::numeric_limits<double>::quiet_NaN());continue;
      }
      V q=mul(sub(p,v[0]),1/length);finite(q);
      w[1]=dot(q,cross(b,c))/determinant;w[2]=dot(a,cross(q,c))/determinant;
      w[3]=dot(a,cross(b,q))/determinant;w[0]=1-w[1]-w[2]-w[3];
      bool outside=false,boundary=false;
      for(int j=0;j<4;++j){require(std::isfinite(w[j]),"Weight overflow");outside|=w[j]<-eps;boundary|=std::abs(w[j])<=eps;}
      states[i]=outside?1:boundary?0:-1;
    }
 });
}
int mc_local_properties(void* handle,double* faces,size_t nf,double* vertices,size_t nv){
 return guard([&]{
    auto& m=get(handle);require(faces&&vertices,"Null buffer");
    require(m.f.size()<=nf/7&&m.v.size()<=nv/2,"Output buffer too small");
    std::fill(vertices,vertices+2*m.v.size(),0.0);
    for(size_t i=0;i<m.f.size();++i){
      auto f=m.f[i];V a=m.v[f[0]],b=m.v[f[1]],c=m.v[f[2]];
      V cr=cross(sub(b,a),sub(c,a));double size=norm(cr);require(std::isfinite(size),"Area overflow");
      for(int k=0;k<3;++k){faces[7*i+k]=a[k]/3+b[k]/3+c[k]/3;faces[7*i+3+k]=size?cr[k]/size:0;}
      faces[7*i+6]=size/2;
      for(auto j:f){vertices[2*j]+=size/6;vertices[2*j+1]+=size/24;}
    }
    for(size_t i=0;i<2*m.v.size();++i)require(std::isfinite(vertices[i]),"Vertex area overflow");
 });
}
int mc_unique_edges(void* handle,int64_t* pairs,size_t np,double* midpoints,size_t nm,size_t* count){
 return guard([&]{
    auto& m=get(handle);require(count,"Null count");
    std::map<std::pair<int64_t,int64_t>,int> edges;
    for(auto f:m.f)for(int j=0;j<3;++j){auto a=f[j],b=f[(j+1)%3];if(a>b)std::swap(a,b);edges[{a,b}]=0;}
    *count=edges.size();
    if(!pairs&&!midpoints&&np==0&&nm==0)return;
    require(pairs&&midpoints,"Null buffer");require(edges.size()<=np/2&&edges.size()<=nm/3,"Output buffer too small");
    size_t i=0;for(auto e:edges){auto a=e.first.first,b=e.first.second;pairs[2*i]=a;pairs[2*i+1]=b;
      for(int k=0;k<3;++k)midpoints[3*i+k]=m.v[a][k]/2+m.v[b][k]/2;
      ++i;
    }
 });
}
}
