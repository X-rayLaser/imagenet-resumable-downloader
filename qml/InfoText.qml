import QtQuick 2.5
import QtQuick.Controls 2.2


Rectangle {
    id: root
    width: parent.width
    height: 40

    property alias label: left_one.text
    property alias value: right_one.text

    Row {
        id: row_id
        spacing: 15
        anchors.horizontalCenter: parent.horizontalCenter
        Text {
            id: left_one
            font.pointSize: 20.5
            font.bold: true
        }

        Text {
            id: right_one
            font.pointSize: 20.5
            font.bold: true
        }
    }
}