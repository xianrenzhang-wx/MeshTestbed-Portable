#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace meshcore {
using V = std::array<double,3>;
using F = std::array<int64_t,3>;
struct Box { V lo,hi; };
struct Node { Box box; size_t begin=0,end=0; int left=-1,right=-1; };
struct Mesh {
    std::vector<V> v;
    std::vector<F> f;
    std::vector<int64_t> reverse;
    std::vector<size_t> order;
    std::vector<Node> tree;
};
extern thread_local std::string error;
inline void require(bool b,const char* message) { if(!b) throw std::runtime_error(message); }
template<class Fn> int guard(Fn fn) noexcept {
    try { error.clear(); fn(); return 0; }
    catch(const std::exception& e) { error=e.what(); return -1; }
    catch(...) { error="Unknown native error"; return -1; }
}
inline Mesh& get(void* p) { require(p,"Mesh is closed or null"); return *static_cast<Mesh*>(p); }
inline V sub(const V& a,const V& b) { return {a[0]-b[0],a[1]-b[1],a[2]-b[2]}; }
inline V add(const V& a,const V& b) { return {a[0]+b[0],a[1]+b[1],a[2]+b[2]}; }
inline V mul(const V& a,double x) { return {a[0]*x,a[1]*x,a[2]*x}; }
inline V cross(const V& a,const V& b) { return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]}; }
inline double dot(const V& a,const V& b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
inline double norm(const V& a) { return std::hypot(a[0],a[1],a[2]); }
inline void finite(const V& p) { for(double x:p) require(std::isfinite(x),"Non-finite vertex"); }
inline V read3(const double* p) { require(p,"Null coordinate");V v{p[0],p[1],p[2]};finite(v);return v; }
inline void tolerance(double t) {require(std::isfinite(t)&&t>=0,"Tolerance must be finite and nonnegative");}
}
