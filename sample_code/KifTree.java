import java.io.InputStream;
import java.io.InputStreamReader;
import com.nttdocomo.io.BufferedReader;
import javax.microedition.io.Connector;

import java.util.Vector;
import java.util.Enumeration;

public class KifTree {
	public static KifTree root = null;
	KifTree parent;
	String lastMove;  //what move leads this
	Vector nextMove;  //次の手

	static final boolean useSibling = false;
	KifTree sibling;  //次の手が10以上になる場合の振り替え先

	Vector labeledNode;

	int lineNo;  //棋譜ファイル上の行番号、最終手に保存

	KifTree() {
		parent = null;
		lastMove = "";
		nextMove = new Vector();
		labeledNode = new Vector();
	}
	
	KifTree(KifTree parent, String move) {
		this.parent = parent;
		this.lastMove = move;
		nextMove = new Vector();
	}

	public static void init() {
		if (KifTree.root == null){
			KifTree.root = new KifTree();
		}
	}

	public static void removeAllKifs() {
		KifTree.root.nextMove = new Vector();
	}

	public static boolean isEmpty() {
		return (KifTree.root.nextMove.size() == 0);
	}
	
	//ファイル等からの棋譜読み込み
	public static void loadKifs(InputStream is) {
		InputStreamReader isr = null;
		BufferedReader br = null;
		try{
			isr = new InputStreamReader(is);  
			br = new BufferedReader(isr);

			String line = null;
			String score[] = new String[300];
			int n = 0;
			int lineCount = 0;

			while((line = br.readLine()) != null) {
				lineCount++;
				if (line.equals("EOF")) break;  //スクラッチパッドなら"EOF"行まで

				score[n++] = line;
				if (line.equals("")){  //空行は1つの棋譜の終わりとみなす
					if (n > 1){
						score[n-2] += "\t#line " + (lineCount - 1);
						root.add(score);
					}
					score = new String[300];
					n = 0;
				}
			}
			if (n > 1){
				score[n-2] += "\t#line " + (lineCount - 1);
				root.add(score);
			}
		}
		catch(Exception e) {
			System.out.println(e.getMessage());
			e.printStackTrace();
		}
		finally {
			try {
				is.close();
				isr.close();
				br.close();
			} catch(Exception e) {}
		}
  	}

	public String move() {
		return this.lastMove;
	}

	public KifTree get(int i) {
		if (i >= nextMove.size()) return null;
		return (KifTree)nextMove.elementAt(i);
	}

	public KifTree getNext(String move) {  //最初に見つかったノードを返す
		Enumeration itor = nextMove.elements();
		while(itor.hasMoreElements()){
			KifTree k = (KifTree)itor.nextElement();
			if (k.move().equals(move)) return k;
		}
		return null;
	}

	public int getNumOfNext() {
		return nextMove.size();
	}

	public KifTree getParent() {
		return parent;
	}

	public KifTree add(String move) {
		KifTree k = this.getNext(move);
		if (k == null){
			k = new KifTree(this, move);
			if (!useSibling || nextMove.size() < 9)
				nextMove.addElement(k);
			else{
				//10以上の選択肢があれば2ノードに分ける
				if (sibling == null) {
					//まだ分けられていなければ、親に弟ノードを追加する
					sibling = new KifTree(this.parent, this.lastMove);
					this.parent.nextMove.addElement(sibling);
				}
				k = sibling.add(move);
			}
		}
		return k;
	}

	public void add(String[] move) {
		KifTree k = KifTree.root;
		int i = 0;
		String lastPos = "";  //「同」の解決用
		boolean resolveDou = false;
		while (!move[i].equals("")) {
			String[] strs = mySplit(move[i]);  //符号の後に何か置けるようにした
			String code = strs[0];  // 最初のtokenが符号
			int label = 0, merge = 0, line = 0;
			if (strs[1] != null && strs[1].equals("#label")) {
				label = Integer.valueOf(strs[2]).intValue();
			}
			if (strs[1] != null && strs[1].equals("#merge")) {
				merge = Integer.valueOf(strs[2]).intValue();
			}
			if (strs[1] != null && strs[1].equals("#line")) {
				line = Integer.valueOf(strs[2]).intValue();
			}
			
			//k = k.add(move[i]);
			if (resolveDou && code.charAt(1) == '同') {
				// 「同」の部分を直前の数字部分に置換
				int nextIndex = 2;
				while(code.charAt(nextIndex) == '　') nextIndex++;
				code = code.substring(0, 1) + lastPos + code.substring(nextIndex);
			}
			k = k.add(code);

			if (code.charAt(1) != '同')
				lastPos = code.substring(1,3);  // 数字部分を保存

			if (label > 0){  // この手を指した後の局面へのラベル付け
				if (label >= labeledNode.size())
					labeledNode.setSize(label+1);
				labeledNode.setElementAt(k, label);
				//System.out.println(k.lastMove + ": label " + label + " registered");
				//System.out.println("labeledNode has " + labeledNode.size() + " elements, " + ((KifTree) labeledNode.elementAt(label)).lastMove + " at " + label );
			}
			if (merge > 0){  // この手を指した後の局面をラベルした局面に繋げる
				//マージはnextMove（子ノード）の共有によって行う
				k.nextMove = ((KifTree) labeledNode.elementAt(merge)).nextMove;
				//System.out.println(k.lastMove + ": merged label " + merge + " (r" + ((KifTree) labeledNode.elementAt(merge)).lastMove + ")");
			}
			if (line > 0){
				k.lineNo = line;
				//System.out.println(k.lastMove + ": lineNo=" + line);
			}
			
			// 合流直後の「同」はどちらから来ても良いように解決しておく
			if (label > 0 || merge > 0)
				resolveDou = true;
			else
				resolveDou = false;

			i++;
		}
	}

	public boolean remove(KifTree node) {
		return nextMove.removeElement(node);
	}

	//String#split(string, " \t")がCLDCに無いので、代わりを作る
	private static String[] mySplit(String line) {
		String[] result = new String[4];
		int begin = 0, end;
		for (int i = 0; i < 4; i++) {
			for(; begin < line.length() && " \t".indexOf(line.charAt(begin)) >= 0; begin++);
			if (begin >= line.length())
				break;
			for(end = begin; end < line.length() && " \t".indexOf(line.charAt(end)) < 0; end++);
			result[i] = line.substring(begin, end);
			begin = end;
		}
		return result;
	}

	//スクラッチパッドにてチェック済とされている棋譜を削除する
	public static void removeChecked(Vector checked){  //String vector
		int removeLine[] = new int[checked.size()];

		//"(line %d)"部分の%dのリストを作る
		for (int i = 0; i < checked.size(); i++) {
			String s = (String)checked.elementAt(i);
			int i1 = s.indexOf("(line ");
			int i2 = s.indexOf(")", i1);
			if (i1 >= 0 && i2 > i1) {
				removeLine[i] = Integer.valueOf(s.substring(i1+6, i2)).intValue();
				System.out.println("checked[" + i + "] = " + Integer.valueOf(s.substring(i1+6, i2)));
			}
		}

		removeList = removeLine;
		checkedValue = !checkedValue;
		checkAndRemove(root);

		//ループにしか繋がらない枝を削除する
		checkedValue = !checkedValue;
		removeLoopOnly(root);
	}

	private static int[] removeList;
	private boolean checkedFlag = false;
	static private boolean checkedValue = false;
	//特定のlineNoに至るノードを再帰的に削除する
	private static boolean checkAndRemove(KifTree node) {
		//ループ対策として、探索されたノードのフラグを設定された値にする
		if (node.checkedFlag == checkedValue) return false;
		node.checkedFlag = checkedValue;

		if (node.nextMove.size() == 0) {  //末端ノードなら
			for (int i = 0; i < removeList.length; i++) {
				if (node.lineNo == removeList[i]) {
					System.out.println("Removing " + node.lastMove);
					return true;
				}
			}
			return false;
		}

		//再帰的に検索する
		//Iteratorを使ってもiterate中にremoveするとおかしくなるので、末尾から検索して削除する
		for (int i = node.nextMove.size()-1; i >= 0; i--) {
			//System.out.println("node " + node.lastMove + ": searching " + i + "/" + node.nextMove.size());
			if (i >= node.nextMove.size()) continue;  //削除中にnextMoveが減った場合の対策
			if (checkAndRemove((KifTree)node.nextMove.elementAt(i)))
				node.nextMove.removeElementAt(i);
		}

		if (node.nextMove.size() == 0)
			return true;
		return false;
	}

	//ループにしか繋がらない枝を削除する
	//Memo: #mergeラベルを付ける時にループができることを検出するのは難しいし
	//      実際にループ手順はあるのだから間違っていない
	//      削除時にループごと消すのが妥当だと考える
	private boolean checking = false;
	private boolean onlyLoopAfterThis = false;  //この先ループのみ、を示す
	private static boolean removeLoopOnly(KifTree node) {
		if (node.checking) return false;  //ループ発見
		if (node.onlyLoopAfterThis) return false;  //この先ループのみ

		//ループ対策として、探索されたノードのフラグを設定された値にする
		if (node.checkedFlag == checkedValue) return true;
		node.checkedFlag = checkedValue;
		
		if (node.nextMove.size() == 0) {  //末端ノードなら
			return true;  //ループでない
		}

		boolean anyLeaf = false;
		node.checking = true;  //検索中のパスである印
		//再帰的に検索する
		for (int i = node.nextMove.size()-1; i >= 0; i--) {
			KifTree child = (KifTree)node.nextMove.elementAt(i);
			if (removeLoopOnly(child))
				anyLeaf = true;  //1つでもループでない枝があればOK
		}
		node.checking = false;

		if (anyLeaf) {
			//ループにしか繋がらない枝とそうでない枝が混在するノードにて
			//ループにしか繋がらない枝を切り離す
			for (int i = node.nextMove.size() - 1; i >= 0; i--) {
				KifTree child = (KifTree)node.nextMove.elementAt(i);
				if (child.onlyLoopAfterThis) {
					System.out.println("removing " + child.lastMove);
					node.nextMove.removeElementAt(i);
				}
			}
			return true;
		}

		System.out.println("node " + node.lastMove + ": loop only branch found!");
		//ループに繋がる枝しか無いノードである
		node.onlyLoopAfterThis = true;
		//このノードを含めて切り離すので、ここでは削除しない

		return false;
	}

	//空行区切りの全棋譜を返す
	public static String getAllKifs() {
		allKifs = "";
		searchAllKifs(root, "");
		String tmp = allKifs;
		allKifs = null;
		return tmp;
	}
	private static String allKifs;
	private static void searchAllKifs(KifTree node, String kifsSoFar) {
		if (!node.lastMove.equals(""))
			kifsSoFar += node.lastMove + "\n";
		if (node.nextMove.size() == 0) {
			allKifs += kifsSoFar + "\n";
		} else {
			for (int i=0; i<node.nextMove.size(); i++) {
				searchAllKifs((KifTree)node.nextMove.elementAt(i), kifsSoFar);
			}
		}
	}
}
