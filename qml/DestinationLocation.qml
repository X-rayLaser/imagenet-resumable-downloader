import QtQuick 2.5
import QtQuick.Controls 2.2
import QtQuick.Dialogs 1.0


Rectangle {
    id: root
    width: parent.width

    property string download_path: ""

    FileDialog {
        id: fileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        selectFolder: true

        onAccepted: {
            root.download_path = String(fileDialog.fileUrls[0]);
        }
    }

    Row {
        width: parent.width
        spacing: 15
        Text {
            text: "Download path"
        }
        Text {
            text: root.download_path
        }

        Button {
            text: "Choose"
            onClicked: {
                fileDialog.open();
                fileDialog.visible = true;
            }
        }
    }
}