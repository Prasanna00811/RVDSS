import java.util.*;
public class Main{
    public static void main(String [] args){
        Scanner sc = new Scanner(System.in);
        int Q = sc.nextInt();
        TreeSet<Integer> set = new TreeSet<>();
        for(int i = 0; i < Q; i++){
            int X = sc.nextInt();
            int Y = sc.nextInt();
            if(X == 0){
                set.add(Y);
            }else{
                if(set.contains(Y)){
                    System.out.print("1");
                set.remove(Y);
                }
                System.out.print("0");
            }
            

        }


        }
    }
