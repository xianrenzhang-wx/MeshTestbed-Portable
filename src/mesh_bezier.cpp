// Cubic and tensor-product bicubic Bernstein evaluation for Homework 6.
#include "mesh_core.h"
#include "mesh_internal.h"
#include <array>

using namespace meshcore;
namespace {
std::array<long double,4> basis(size_t k,size_t n) {
    const long double t=static_cast<long double>(k)/n,s=1-t;
    return {s*s*s,3*t*s*s,3*t*t*s,t*t*t};
}
void subdivisions(size_t n) {require(n>=1&&n<=1000,"Subdivisions must be between 1 and 1000");}
void controls_valid(const double* p,size_t n) {
    require(p,"Null control points");
    for(size_t i=0;i<n;++i) require(std::isfinite(p[i]),"Non-finite control point");
}
}
extern "C" {
int mc_bezier_curve(const double* cp,size_t n,double* out,size_t elements) {
    return guard([&]{
        subdivisions(n);controls_valid(cp,12);
        require(out&&elements>=3*(n+1),"Curve output buffer too small");
        for(size_t a=0;a<=n;++a) {
            const auto w=basis(a,n);
            for(size_t k=0;k<3;++k) {
                long double value=0;
                for(size_t i=0;i<4;++i) value+=w[i]*cp[3*i+k];
                out[3*a+k]=static_cast<double>(value);
                require(std::isfinite(out[3*a+k]),"Curve coordinate overflow");
            }
        }
    });
}
int mc_bezier_surface(const double* cp,size_t nu,size_t nv,double* out,size_t elements,
                      int64_t* faces,size_t face_elements) {
    return guard([&]{
        subdivisions(nu);subdivisions(nv);controls_valid(cp,48);
        require(out&&elements>=3*(nu+1)*(nv+1),"Surface output buffer too small");
        require(faces&&face_elements>=6*nu*nv,"Face output buffer too small");
        for(size_t a=0;a<=nu;++a) for(size_t b=0;b<=nv;++b) {
            const auto wu=basis(a,nu),wv=basis(b,nv);
            const size_t index=a*(nv+1)+b;
            for(size_t k=0;k<3;++k) {
                long double value=0;
                for(size_t i=0;i<4;++i) for(size_t j=0;j<4;++j)
                    value+=wu[i]*wv[j]*cp[3*(4*i+j)+k];
                out[3*index+k]=static_cast<double>(value);
                require(std::isfinite(out[3*index+k]),"Surface coordinate overflow");
            }
        }
        size_t f=0;
        for(size_t a=0;a<nu;++a) for(size_t b=0;b<nv;++b) {
            const int64_t p=static_cast<int64_t>(a*(nv+1)+b),q=p+static_cast<int64_t>(nv+1);
            for(int64_t v:{p,q,q+1,p,q+1,p+1}) faces[f++]=v;
        }
    });
}
}
