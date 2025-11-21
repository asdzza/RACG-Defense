use ndarray_v2::array;   // ❌ use ndarray::array;

fn main() {
    let a = array![1, 2, 3];
    println!("{:?}", a.mean().unwrap());
}
