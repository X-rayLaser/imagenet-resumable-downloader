import QtQuick 2.5

Rectangle {
    radius: 5
    width: parent.width
    height: 50

    property alias toastVisible: text.visible

    Text {
        id: text
        text: "Download is complete!"
        font.pointSize: 20.5
        font.bold: true
        visible: false

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
    }
}