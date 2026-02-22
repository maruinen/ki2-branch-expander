/*
 * iKifuPlayer.java
 */
import com.nttdocomo.ui.*;

import java.util.Vector;

import java.io.*;				 // DataOutputStreamクラスのため
import javax.microedition.io.*;  // Connectorクラスのため

/* ToDo:
   ・棋譜データをSDカードから読み込めるようにしたい
     確かJPEGに偽装すればテキストファイルを読み込めるのではなかったか
*/

/**
 * iKifuPlayer
 *
 * @author maruinen
 */
public class iKifuPlayer extends IApplication {

	public void start() {
		/*
		 * The program of IApplication is written here.
		 */
		KifTree.init();
		try {
			InputStream is = Connector.openInputStream("resource:///Kifs.txt");
			KifTree.loadKifs(is);
		} catch(Exception e) {
			System.out.println(e.getMessage());
			e.printStackTrace();
		}

		Display.setCurrent((Frame)new MainPanel());
	}
}


/**
 * MainPanel
 * 
 */
class MainPanel extends Panel implements SoftKeyListener, KeyListener{
	SubPanel subPanel = new SubPanel((Frame)this);

	ImageLabel boardComponent;
	TextBox textBox;
	Board board;
	KifTree current = null;
	Vector history = null;  //vector of KifTree
	KifTree backFrom = null;
	int pageOfChoice;

	MainPanel() {
		setTitle("maruinenさん家の将棋盤");

		setSoftLabel(SOFT_KEY_1, "END");
		setSoftLabel(SOFT_KEY_2, "MENU");
		setSoftKeyListener((SoftKeyListener)this);
		
		setKeyListener((KeyListener)this);

		//board = new Board();
		//boardComponent = new ImageLabel(board.image);
		boardComponent = new ImageLabel();
		this.add(boardComponent);

		textBox = new TextBox("", 40, 9, TextBox.DISPLAY_ANY);
		textBox.setEditable(false);
		//textBox.setEnabled(false);  //これすると灰色になってしまう
		this.add(textBox);

		//resetBoard();
		//history = new Vector();
		//refreshText();
		
		//少し汚いが、きれいに動くので、上の3行に代えて、これで初期化する
		keyReleased(this, Display.KEY_CLEAR);
	}

	public void softKeyPressed(int softKey) {
	}
	
	public void softKeyReleased(int softKey) {
		if (softKey == SOFT_KEY_1) {
			IApplication.getCurrentApp().terminate();
		}
		if (softKey == SOFT_KEY_2) {
			if (current.getNumOfNext() == 0) {
				String kif = "";
				KifTree node;
				for(int i=0; i<history.size(); i++){
					node = (KifTree)history.elementAt(i);
					if (!kif.equals("")) kif += "\n";
					kif += node.lastMove;
					if (node.lineNo > 0) {
						kif += "        (line " + node.lineNo + ")";
					}
				}
				subPanel.append(kif);
			}
			Display.setCurrent((Frame)subPanel);
		}
	}

	public void keyPressed(Panel panel, int key) {
		//邪魔なのでソフトキー表示を消す
		setSoftLabel(SOFT_KEY_1, null);
		setSoftLabel(SOFT_KEY_2, null);
	}

	public void keyReleased(Panel panel, int key) {
		KifTree next = null;
		int choice = 0;
		KifTree backFromTmp = null;
		switch (key) {
		case Display.KEY_8: choice++;
		case Display.KEY_7: choice++;
		case Display.KEY_6: choice++;
		case Display.KEY_5: choice++;
		case Display.KEY_4: choice++;
		case Display.KEY_3: choice++;
		case Display.KEY_2: choice++;
		case Display.KEY_1: 
			next = current.get(pageOfChoice * 8 + choice);
			break;
		case Display.KEY_9:
			//ページ切替
			pageOfChoice++;
			backFromTmp = backFrom;
			break;
		case Display.KEY_ASTERISK:
			//1手戻す
			//…の代わりに、最初から1手前まで進める
			if (history.size() > 0) {
				backFromTmp = (KifTree)history.elementAt(history.size() - 1);
				history.removeElementAt(history.size() - 1);
				resetBoard();
				for(int i=0; i<history.size(); i++){
					current = (KifTree)history.elementAt(i);
					board.move1(current.move());
				}
			}
			break;
		case Display.KEY_POUND:
			if (current.getNumOfNext() == 1) {  //１本道なら
				//分岐点か終点まで早送り再生する
				while(current.getNumOfNext() == 1){
					keyReleased(panel, Display.KEY_1);
				}
			}else{
				//分岐点まで戻る
				for(int i=history.size()-1; i > 0; i--){
					KifTree tmp = (KifTree)history.elementAt(i);
					if (tmp.getParent().getNumOfNext() > 1)
						break;
					history.removeElementAt(i);
				}
				keyReleased(panel, Display.KEY_ASTERISK);
				return;
			}
			break;
		//Display.KEY_CLEARは「ｉアプリオプションAPI」、サポートしない端末がある
		case Display.KEY_CLEAR:  //P-01CではCLEARボタンは効かない
		case Display.KEY_0:      //仕方ないので0ボタンを使う
			//初期状態に戻る
			resetBoard();
			history = new Vector();
			backFrom = null;
			pageOfChoice = 0;
			break;
		default:
			return;
		}

		backFrom = backFromTmp;
		
		if (next != null){
			board.move1(next.move());
			current = next;
			history.addElement(current);
		}

		if (pageOfChoice * 8 >= current.getNumOfNext())
			pageOfChoice = 0;
		
		refreshText();

		//盤面のちらつきの抑制のため、これをなるべく遅らせる
		boardComponent.setImage(board.image);
	}

	void resetBoard() {
		board = new Board();
		//boardComponent.setImage(board.image);  //ここで済ませたいが、ちらつき抑制のため遅延
		current = KifTree.root;
	}

	void refreshText() {
		String s = "";
		boolean komaochi = history.size() > 0 && Board.isKomaochiCode(((KifTree)history.firstElement()).move());
		int komaochi_adj =  komaochi ? 1 : 0;
		if (current != KifTree.root)
			if  (komaochi && history.size() == 1)
				s += ((KifTree)history.firstElement()).move() + "\n";
			else
				s += (history.size() - komaochi_adj) + "手目 " + current.move() + "まで\n";

		s += (history.size() + 1 - komaochi_adj) + "手目の選択肢:\n";
		for(int i=0; pageOfChoice * 8 + i < current.getNumOfNext() && i<8; i++){
			s += (i+1) + ": " + current.get(pageOfChoice * 8 + i).move() +
				//3列表示、5つ以下なら1列表示
				(i%3 == 2 || current.getNumOfNext() <= 5 ? "\n" : "  ");
		}
		if (current.getNumOfNext() > 8){
			s += "9: 次のページへ\n";
		}
		if (backFrom != null && current.getNumOfNext() > 1){
			s += "\n（前回の選択: " + backFrom.move() + "）\n";
		}
		textBox.setText(s);
	}
}

/**
 * SubPanel
 * 
 */
class SubPanel extends Panel implements SoftKeyListener, KeyListener, ComponentListener {
	Frame backTo;
	ListBox listBox;
	TextBox textBox;
	int textNo = 0;		//textBoxに表示する棋譜の番号
						//ListBoxのカーソル位置を取得する手段が見つからないので、それを使うことも同期することもできない
	Button removeUnmarkedButton;
	Button allClrButton;

	SubPanel(Frame from) {
		backTo = from;
		
		setTitle("Sub menu");

		setSoftLabel(SOFT_KEY_1, "Checked");
		setSoftLabel(SOFT_KEY_2, "Back");
		setSoftKeyListener((SoftKeyListener)this);

		setKeyListener((KeyListener)this);

		setComponentListener((ComponentListener)this);
		
		listBox = new ListBox(ListBox.CHECK_BOX, 8);
		this.add(listBox);
		
		textBox = new TextBox("", 40, 15, TextBox.DISPLAY_ANY);
		textBox.setEditable(false);
		this.add(textBox);

		this.add(new Label("4,6で切替　"));

		removeUnmarkedButton = new Button("非選択項目クリア");
		this.add(removeUnmarkedButton);
		
		allClrButton = new Button("全クリア");
		this.add(allClrButton);
		
		loadList();
		updateText();
	}

	public void softKeyPressed(int softKey) {
	}
	
	public void softKeyReleased(int softKey) {
		if (softKey == SOFT_KEY_1) {
			//チェック済棋譜を削除する
			int num = listBox.getItemCount();
			Vector checked = new Vector();
			for (int i = 0; i < num; i++) {
				checked.addElement(listBox.getItem(i));
			}
			KifTree.removeChecked(checked);
			Display.setCurrent(backTo);
		}
		if (softKey == SOFT_KEY_2) {
			Display.setCurrent(backTo);
		}
	}
	
	public void keyPressed(Panel panel, int key) {
	}

	public void keyReleased(Panel panel, int key) {
		switch (key) {
// 		case Display.KEY_LEFT:	//cursor key is not listened
		case Display.KEY_4:
			if (textNo > 0) textNo--;
			break;
// 		case Display.KEY_RIGHT:	//cursor key is not listened
		case Display.KEY_6:
			if (textNo < listBox.getItemCount() - 1) textNo++;
			break;
		default:
		}
		updateText();
	}

	boolean listBox_changing = false;
	public void componentAction(Component source, int type, int param) {
		if (source == listBox && type == SELECTION_CHANGED) {
			if (!listBox_changing) {
				saveList();
				updateText();
			}
		}

		if (source == removeUnmarkedButton && type == BUTTON_PRESSED) {
			/* 非選択項目を削除 */
			Vector tmp = new Vector();
			for (int i = 0; i < listBox.getItemCount(); i++)
				if (listBox.isIndexSelected(i))
					tmp.addElement(listBox.getItem(i));
			listBox_changing = true; /* componentActionの保存を抑止 */
			listBox.removeAll();
			for (int i = 0; i < tmp.size(); i++) {
				listBox.append((String)tmp.elementAt(i));
				listBox.select(i);
			}
			listBox_changing = false;
			saveList();
			if (textNo >= listBox.getItemCount())
				textNo = listBox.getItemCount() - 1;
			updateText();
		}

		if (source == allClrButton && type == BUTTON_PRESSED) {
			/* リストを全て削除 */
			listBox_changing = true; /* componentActionの保存を抑止 */
			listBox.removeAll();
			listBox_changing = false;
			saveList();
			updateText();
		}
	}

	void loadList() {
		try {
			// スクラッチパッドを読み込み用にオープンする
			DataInputStream in = Connector.openDataInputStream("scratchpad:///0");
			int num = in.readInt();
			for(int i = 0; i < num; i++){
				int status = in.readByte();
				listBox.append(in.readUTF());
				if (status == 1)
					listBox.select(i);
			}
			in.close();
		}
		catch (Exception e) {
			System.err.println("read error");
		}
	}

	synchronized void saveList() {
		try {
			// スクラッチパッドを書き込み用にオープンする
			DataOutputStream out = Connector.openDataOutputStream("scratchpad:///0");

			int num = listBox.getItemCount();
			out.writeInt(num);
			for(int i = 0; i < num; i++){
				if (listBox.isIndexSelected(i)) {
					out.writeByte(1);
				} else {
					out.writeByte(0);
				}
				out.writeUTF(listBox.getItem(i));
			}
			
			// スクラッチパッドをクローズする
			out.close();
		}
		catch (Exception e) {
			// エラーメッセージを表示する
			// エミュレータ環境でのみ確認できる
			System.err.println("write error" + e);
		}
	}		

	void updateText() {
		if (textNo < listBox.getItemCount()) {
			textBox.setText(listBox.getItem(textNo));
			if (listBox.isIndexSelected(textNo))
				textBox.setEnabled(true);
			else
				textBox.setEnabled(false);
		} else {
			textBox.setText("");
			textBox.setEnabled(false);
		}
	}

	public void append(String kif) {
		int lastIndex = kif.lastIndexOf('\n');
		lastIndex = kif.lastIndexOf('\n', lastIndex - 1);
		lastIndex = kif.lastIndexOf('\n', lastIndex - 1);
		String tail = kif.substring(lastIndex + 1);
		kif = "…\n" + tail + "\n\n" + kif;
		
		for (textNo = 0; textNo < listBox.getItemCount(); textNo++)
			if (listBox.getItem(textNo).equals(kif)) break;
		if (textNo == listBox.getItemCount()) {
			listBox.append(kif);
			listBox.select(textNo);
		}
		saveList();
		updateText();
	}
}

