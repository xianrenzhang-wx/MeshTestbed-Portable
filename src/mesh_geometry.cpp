// Independent implementations of triangle geometry and tetrahedral moments.
// Mathematical references and numeric limitations are listed in GEOMETRY.md.
#include "mesh_core.h"
#include "mesh_internal.h"
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <queue>
#include <tuple>

namespace meshcore {
using Tri=std::array<V,3>;
using Segment=std::array<V,2>;
Tri triangle(const Mesh& m,size_t i) {const auto& f=m.f[i];return {m.v[f[0]],m.v[f[1]],m.v[f[2]]};}
Box bounds(const Tri& t) {
    Box b{t[0],t[0]};
    for(const auto& p:t) for(int k=0;k<3;++k) {b.lo[k]=std::min(b.lo[k],p[k]);b.hi[k]=std::max(b.hi[k],p[k]);}
    return b;
}
Box combine(Box a,const Box& b) {
    for(int k=0;k<3;++k) {a.lo[k]=std::min(a.lo[k],b.lo[k]);a.hi[k]=std::max(a.hi[k],b.hi[k]);}return a;
}
int build_tree(Mesh& m,size_t begin,size_t end) {
    Box b=bounds(triangle(m,m.order[begin]));
    for(size_t i=begin+1;i<end;++i) b=combine(b,bounds(triangle(m,m.order[i])));
    int id=static_cast<int>(m.tree.size()); m.tree.push_back({b,begin,end,-1,-1});
    if(end-begin>8) {
        int axis=0;for(int k=1;k<3;++k) if(b.hi[k]-b.lo[k]>b.hi[axis]-b.lo[axis]) axis=k;
        size_t mid=begin+(end-begin)/2;
        std::nth_element(m.order.begin()+begin,m.order.begin()+mid,m.order.begin()+end,[&](size_t a,size_t c){
            auto x=bounds(triangle(m,a)), y=bounds(triangle(m,c));
            return x.lo[axis]*0.5+x.hi[axis]*0.5 < y.lo[axis]*0.5+y.hi[axis]*0.5;
        });
        int left=build_tree(m,begin,mid),right=build_tree(m,mid,end);
        m.tree[id].left=left;m.tree[id].right=right;
    }
    return id;
}
void ensure_tree(Mesh& m) {
    if(!m.tree.empty()) return;
    require(m.f.size()<size_t(std::numeric_limits<int>::max()/2),"Mesh too large for spatial index");
    m.order.resize(m.f.size());std::iota(m.order.begin(),m.order.end(),size_t(0));
    try {build_tree(m,0,m.order.size());}
    catch(...) {m.tree.clear();m.order.clear();throw;}
}
void nondegenerate(const Mesh& m) {
    for(size_t i=0;i<m.f.size();++i) {
        auto t=triangle(m,i);double area2=norm(cross(sub(t[1],t[0]),sub(t[2],t[0])));
        require(std::isfinite(area2)&&area2>0,"Operation requires nondegenerate triangles without overflow");
    }
}
void closed(const Mesh& m) {
    for(auto r:m.reverse) require(r>=0,"Operation requires a closed, consistently oriented mesh");
    nondegenerate(m);
}
double box_distance2(const Box& b,const V& p) {
    double d=0;for(int k=0;k<3;++k) {double x=std::max({b.lo[k]-p[k],0.,p[k]-b.hi[k]});d+=x*x;}return d;
}
double box_distance2(const Box& a,const Box& b) {
    double d=0;for(int k=0;k<3;++k) {double x=std::max({a.lo[k]-b.hi[k],0.,b.lo[k]-a.hi[k]});d+=x*x;}return d;
}
bool boxes_overlap(const Box& a,const Box& b,double eps) {
    for(int k=0;k<3;++k) if(a.lo[k]-b.hi[k]>eps || b.lo[k]-a.hi[k]>eps) return false;
    return true;
}
V closest_segment(const V& p,const V& a,const V& b) {
    auto u=sub(b,a);double d=dot(u,u);
    return d==0?a:add(a,mul(u,std::clamp(dot(sub(p,a),u)/d,0.,1.)));
}
V closest_triangle(const V& p,const Tri& t) {
    V best=t[0];double best2=dot(sub(p,best),sub(p,best));
    for(int k=0;k<3;++k) {
        V q=closest_segment(p,t[k],t[(k+1)%3]);double d=dot(sub(p,q),sub(p,q));
        if(d<best2) {best=q;best2=d;}
    }
    V u=sub(t[1],t[0]),v=sub(t[2],t[0]),n=cross(u,v);double nn=dot(n,n);
    if(nn>0) {
        V w=sub(p,t[0]);double a=dot(cross(w,v),n)/nn,b=dot(cross(u,w),n)/nn;
        if(a>=0&&b>=0&&a+b<=1) {
            V q=add(t[0],add(mul(u,a),mul(v,b)));double d=dot(sub(p,q),sub(p,q));
            if(d<best2) best=q;
        }
    }
    return best;
}
struct Nearest {double d2=std::numeric_limits<double>::infinity();V p{};int64_t face=-1;};
Nearest nearest(Mesh& m,const V& p) {
    ensure_tree(m);Nearest best;
    using Item=std::pair<double,int>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
    queue.push({0,0});
    while(!queue.empty()) {
        auto [d,id]=queue.top();queue.pop();if(d>best.d2) break;
        const auto& node=m.tree[id];
        if(node.left<0) {
            for(size_t i=node.begin;i<node.end;++i) {
                size_t f=m.order[i];V q=closest_triangle(p,triangle(m,f));double qd=dot(sub(p,q),sub(p,q));
                if(qd<best.d2 || (qd==best.d2&&static_cast<int64_t>(f)<best.face)) best={qd,q,static_cast<int64_t>(f)};
            }
        } else for(int child:{node.left,node.right}) {
            double cd=box_distance2(m.tree[child].box,p);if(cd<=best.d2) queue.push({cd,child});
        }
    }
    require(best.face>=0&&std::isfinite(best.d2),"Distance overflow; rescale coordinates");return best;
}
// Sum signed solid angles. Orientation may be entirely reversed. Nested cavities
// require opposite orientation. Deliberately not claimed to be a fast winding tree.
bool inside(const Mesh& m,const V& p) {
    long double total=0;
    for(size_t i=0;i<m.f.size();++i) {
        auto t=triangle(m,i);V a=sub(t[0],p),b=sub(t[1],p),c=sub(t[2],p);
        double la=norm(a),lb=norm(b),lc=norm(c);
        if(la==0||lb==0||lc==0) return true;
        a=mul(a,1/la);b=mul(b,1/lb);c=mul(c,1/lc);
        total+=2*std::atan2(static_cast<long double>(dot(a,cross(b,c))),
                           static_cast<long double>(1+dot(a,b)+dot(b,c)+dot(c,a)));
    }
    return std::abs(total)>2*std::acos(-1.L);
}
bool triangles_overlap(const Tri& aa,const Tri& bb,double eps) {
    // Shift coordinates before projection to avoid cancellation after translation.
    Tri a,b;for(int i=0;i<3;++i) {a[i]=sub(aa[i],aa[0]);b[i]=sub(bb[i],aa[0]);}
    std::array<V,3> ea,eb;
    for(int i=0;i<3;++i) {ea[i]=sub(a[(i+1)%3],a[i]);eb[i]=sub(b[(i+1)%3],b[i]);}
    V na=cross(ea[0],ea[1]),nb=cross(eb[0],eb[1]);
    auto separates=[&](V axis) {
        double length=norm(axis);if(length==0) return false;
        axis=mul(axis,1/length);
        double amin=dot(a[0],axis),amax=amin,bmin=dot(b[0],axis),bmax=bmin;
        for(int i=1;i<3;++i) {double x=dot(a[i],axis),y=dot(b[i],axis);
            amin=std::min(amin,x);amax=std::max(amax,x);bmin=std::min(bmin,y);bmax=std::max(bmax,y);}
        return amin-bmax>eps || bmin-amax>eps;
    };
    if(separates(na)||separates(nb)) return false;
    for(auto x:ea) for(auto y:eb) if(separates(cross(x,y))) return false;
    // In-plane normals are necessary when the triangles are coplanar.
    for(auto x:ea) if(separates(cross(na,x))) return false;
    for(auto x:eb) if(separates(cross(nb,x))) return false;
    return true;
}
double segment_distance2(const V& p,const V& q,const V& r,const V& s) {
    V u=sub(q,p),v=sub(s,r),w=sub(p,r);
    double a=dot(u,u),b=dot(u,v),c=dot(v,v),d=dot(u,w),e=dot(v,w);
    double best=std::numeric_limits<double>::infinity();
    for(const auto& x:{p,q}) {V delta=sub(x,closest_segment(x,r,s));best=std::min(best,dot(delta,delta));}
    for(const auto& x:{r,s}) {V delta=sub(x,closest_segment(x,p,q));best=std::min(best,dot(delta,delta));}
    double den=a*c-b*b;
    if(den>0) {
        double t=(b*e-c*d)/den,z=(a*e-b*d)/den;
        if(t>=0&&t<=1&&z>=0&&z<=1) {V delta=sub(add(p,mul(u,t)),add(r,mul(v,z)));best=std::min(best,dot(delta,delta));}
    }
    return best;
}
double triangle_distance2(const Tri& a,const Tri& b) {
    if(triangles_overlap(a,b,0)) return 0;
    double best=std::numeric_limits<double>::infinity();
    for(int i=0;i<3;++i) {
        V x=sub(a[i],closest_triangle(a[i],b)),y=sub(b[i],closest_triangle(b[i],a));
        best=std::min({best,dot(x,x),dot(y,y)});
        for(int j=0;j<3;++j) best=std::min(best,segment_distance2(a[i],a[(i+1)%3],b[j],b[(j+1)%3]));
    }
    return best;
}
bool surface_collision(Mesh& a,Mesh& b,double eps,int64_t* pair) {
    ensure_tree(a);ensure_tree(b);
    std::vector<std::pair<int,int>> stack{{0,0}};
    while(!stack.empty()) {
        auto [i,j]=stack.back();stack.pop_back();const auto& x=a.tree[i];const auto& y=b.tree[j];
        if(!boxes_overlap(x.box,y.box,eps)) continue;
        if(x.left<0&&y.left<0) {
            for(size_t u=x.begin;u<x.end;++u) for(size_t v=y.begin;v<y.end;++v) {
                auto fi=a.order[u],fj=b.order[v];
                if(triangles_overlap(triangle(a,fi),triangle(b,fj),eps)) {pair[0]=fi;pair[1]=fj;return true;}
            }
        } else if(y.left<0||(x.left>=0&&x.end-x.begin>=y.end-y.begin)) {
            stack.push_back({x.left,j});stack.push_back({x.right,j});
        } else {stack.push_back({i,y.left});stack.push_back({i,y.right});}
    }
    return false;
}
bool any_component_inside(const Mesh& a,const Mesh& b) {
    std::vector<bool> seen(a.f.size(),false);
    for(size_t root=0;root<a.f.size();++root) if(!seen[root]) {
        if(inside(b,a.v[a.f[root][0]])) return true;
        std::vector<size_t> todo{root};seen[root]=true;
        while(!todo.empty()) {size_t f=todo.back();todo.pop_back();
            for(int c=0;c<3;++c) {size_t other=static_cast<size_t>(a.reverse[3*f+c])/3;
                if(!seen[other]) {seen[other]=true;todo.push_back(other);}}
        }
    }
    return false;
}
struct Section { std::vector<Segment> segments; };
bool plane_box(const Box& b,const V& origin,const V& normal,double eps) {
    V lo=sub(b.lo,origin),hi=sub(b.hi,origin);double low=0,high=0;
    for(int k=0;k<3;++k) {double a=lo[k]*normal[k],c=hi[k]*normal[k];low+=std::min(a,c);high+=std::max(a,c);}
    return low<=eps&&high>=-eps;
}
std::unique_ptr<Section> section(Mesh& m,const V& origin,const V& normal,double eps) {
    ensure_tree(m);auto out=std::make_unique<Section>();
    std::map<std::pair<int64_t,int64_t>,std::pair<int,bool>> on_edges;
    auto project=[&](const V& p) {return sub(p,mul(normal,dot(sub(p,origin),normal)));};
    auto edge=[&](int64_t i,int64_t j,bool coplanar) {
        auto& e=on_edges[{std::min(i,j),std::max(i,j)}];if(coplanar) ++e.first;else e.second=true;
    };
    std::vector<int> stack{0};
    while(!stack.empty()) {
        int id=stack.back();stack.pop_back();const auto& node=m.tree[id];
        if(!plane_box(node.box,origin,normal,eps)) continue;
        if(node.left>=0) {stack.push_back(node.left);stack.push_back(node.right);continue;}
        for(size_t idx=node.begin;idx<node.end;++idx) {
            const auto& f=m.f[m.order[idx]];std::array<int,3> sign;int zeros=0;
            for(int c=0;c<3;++c) {double d=dot(sub(m.v[f[c]],origin),normal);sign[c]=d>eps?1:(d<-eps?-1:0);zeros+=sign[c]==0;}
            if(zeros>=2) {
                for(int c=0;c<3;++c) if(!sign[c]&&!sign[(c+1)%3]) edge(f[c],f[(c+1)%3],zeros==3);
                continue;
            }
            std::vector<V> hits;
            for(int c=0;c<3;++c) {
                if(sign[c]==0) hits.push_back(project(m.v[f[c]]));
                if(sign[c]*sign[(c+1)%3]<0) {
                    auto i=std::min(f[c],f[(c+1)%3]),j=std::max(f[c],f[(c+1)%3]);
                    double di=dot(sub(m.v[i],origin),normal),dj=dot(sub(m.v[j],origin),normal);
                    hits.push_back(project(add(m.v[i],mul(sub(m.v[j],m.v[i]),di/(di-dj)))));
                }
            }
            if(hits.size()==2&&norm(sub(hits[0],hits[1]))>eps) out->segments.push_back({hits[0],hits[1]});
        }
    }
    for(const auto& item:on_edges) if(item.second.first==1||item.second.second) {
        V a=project(m.v[item.first.first]),b=project(m.v[item.first.second]);
        if(norm(sub(a,b))>eps) out->segments.push_back({a,b});
    }
    return out;
}
}

using namespace meshcore;
extern "C" {
int mc_mass_properties(void* p,double density,double* out,size_t elements) {
    return guard([&]{
        auto& m=get(p);require(out&&elements>=14,"Mass output buffer too small");
        require(std::isfinite(density)&&density>0,"Density must be finite and positive");closed(m);
        V ref=m.v[m.f[0][0]];
        long double vol=0,first[3]{},second[3][3]{};
        for(size_t f=0;f<m.f.size();++f) {
            auto t=triangle(m,f);for(auto& x:t) x=sub(x,ref);
            long double v=static_cast<long double>(dot(t[0],cross(t[1],t[2])))/6;
            vol+=v;long double sum[3]{};
            for(int i=0;i<3;++i) {for(int k=0;k<3;++k) sum[i]+=t[k][i];first[i]+=v*sum[i]/4;}
            for(int i=0;i<3;++i) for(int j=0;j<3;++j) {
                long double diagonal=0;for(int k=0;k<3;++k) diagonal+=static_cast<long double>(t[k][i])*t[k][j];
                second[i][j]+=v*(sum[i]*sum[j]+diagonal)/20;
            }
        }
        require(std::isfinite(vol)&&vol!=0,"Zero or invalid signed volume");
        long double center[3];for(int i=0;i<3;++i) center[i]=first[i]/vol;
        long double orientation=vol>0?1:-1,central[3][3],trace=0;
        for(int i=0;i<3;++i) for(int j=0;j<3;++j) {
            central[i][j]=density*orientation*(second[i][j]-vol*center[i]*center[j]);
            if(i==j) trace+=central[i][j];
        }
        out[0]=static_cast<double>(std::abs(vol));out[1]=out[0]*density;
        for(int i=0;i<3;++i) out[2+i]=static_cast<double>(center[i]+ref[i]);
        for(int i=0;i<3;++i) for(int j=0;j<3;++j) out[5+3*i+j]=static_cast<double>((i==j?trace:0)-central[i][j]);
        for(int i=0;i<14;++i) require(std::isfinite(out[i]),"Mass properties overflow; rescale coordinates");
    });
}
int mc_nearest(void* p,const double* points,size_t n,int signed_distance,double eps,double* result,size_t elements,int64_t* faces,size_t face_elements) {
    return guard([&]{auto& m=get(p);tolerance(eps);
        require(n<=SIZE_MAX/4&&elements>=4*n&&face_elements>=n,"Nearest output buffer too small");
        require(n==0||(points&&result&&faces),"Null nearest buffer");if(signed_distance) closed(m);
        for(size_t i=0;i<n;++i) {
            V q=read3(points+3*i);auto hit=nearest(m,q);double d=std::sqrt(hit.d2);
            if(signed_distance) {if(d<=eps) d=0;else if(inside(m,q)) d=-d;}
            result[4*i]=d;for(int k=0;k<3;++k) result[4*i+1+k]=hit.p[k];faces[i]=hit.face;
        }
    });
}
int mc_classify(void* p,const double* points,size_t n,double eps,int* states,size_t elements) {
    return guard([&]{auto& m=get(p);tolerance(eps);closed(m);
        require(n<=SIZE_MAX/3&&elements>=n&&(n==0||(points&&states)),"Invalid classification buffers");
        for(size_t i=0;i<n;++i) {V q=read3(points+3*i);double d=std::sqrt(nearest(m,q).d2);states[i]=d<=eps?0:(inside(m,q)?-1:1);}
    });
}
int mc_distance(void* p,void* q,double* distance,int64_t* faces,size_t elements) {
    return guard([&]{auto& a=get(p);auto& b=get(q);require(distance&&faces&&elements>=2,"Invalid distance outputs");
        nondegenerate(a);nondegenerate(b);ensure_tree(a);ensure_tree(b);
        double best=std::numeric_limits<double>::infinity();faces[0]=faces[1]=-1;
        using Item=std::tuple<double,int,int>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
        queue.push({0,0,0});
        auto push=[&](int i,int j) {double d=box_distance2(a.tree[i].box,b.tree[j].box);if(d<best) queue.push({d,i,j});};
        while(!queue.empty()) {
            auto [d,i,j]=queue.top();queue.pop();if(d>=best) break;
            const auto& x=a.tree[i];const auto& y=b.tree[j];
            if(x.left<0&&y.left<0) {
                for(size_t u=x.begin;u<x.end;++u) for(size_t v=y.begin;v<y.end;++v) {
                    size_t fi=a.order[u],fj=b.order[v];double td=triangle_distance2(triangle(a,fi),triangle(b,fj));
                    if(td<best) {best=td;faces[0]=fi;faces[1]=fj;}
                }
            } else if(y.left<0||(x.left>=0&&x.end-x.begin>=y.end-y.begin)) {push(x.left,j);push(x.right,j);}
            else {push(i,y.left);push(i,y.right);}
        }
        require(std::isfinite(best),"Mesh distance overflow");*distance=std::sqrt(best);
    });
}
int mc_collision(void* p,void* q,int solid,double eps,int* result,int64_t* pair,size_t elements) {
    return guard([&]{auto& a=get(p);auto& b=get(q);tolerance(eps);require(result&&pair&&elements>=2,"Invalid collision outputs");
        if(solid) {closed(a);closed(b);} else {nondegenerate(a);nondegenerate(b);}
        pair[0]=pair[1]=-1;*result=0;
        if(surface_collision(a,b,eps,pair)) *result=1;
        else if(solid&&(any_component_inside(a,b)||any_component_inside(b,a))) *result=2;
    });
}
int mc_section(void* p,const double* o,const double* n,double eps,void** output) {
    if(output) *output=nullptr;
    return guard([&]{auto& m=get(p);require(output,"Null section output");tolerance(eps);V origin=read3(o),normal=read3(n);
        double length=norm(normal);require(std::isfinite(length)&&length>0,"Plane normal must be nonzero");
        normal=mul(normal,1/length);nondegenerate(m);auto s=section(m,origin,normal,eps);*output=s.release();
    });
}
int mc_section_size(void* p,size_t* n) {return guard([&]{require(p&&n,"Null section");*n=static_cast<Section*>(p)->segments.size();});}
int mc_section_copy(void* p,double* out,size_t elements) {
    return guard([&]{require(p,"Null section");const auto& s=static_cast<Section*>(p)->segments;
        require(s.size()<=SIZE_MAX/6&&elements>=s.size()*6&&(s.empty()||out),"Section buffer too small");
        for(size_t i=0;i<s.size();++i) for(int j=0;j<2;++j) for(int k=0;k<3;++k) out[6*i+3*j+k]=s[i][j][k];
    });
}
void mc_section_destroy(void* p) {delete static_cast<Section*>(p);}
}
